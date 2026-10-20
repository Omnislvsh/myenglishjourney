function eventElement(event) {
  return event.target instanceof Element ? event.target : document.body;
}

document.addEventListener("keydown", (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  if (document.querySelector("[data-quiz]")) return;

  if (eventElement(event).closest("input, textarea, select, [contenteditable]")) return;

  const selectors = {
    ArrowLeft: ".md-footer__link--prev",
    ArrowRight: ".md-footer__link--next",
  };
  const selector = selectors[event.key];
  if (!selector) return;

  const link = document.querySelector(selector);
  if (link) link.click();
});

document.addEventListener("input", (event) => {
  if (!event.target.matches(".word-filter")) return;

  const query = event.target.value.trim().toLowerCase();
  document.querySelectorAll(".word-grid .word").forEach((word) => {
    word.hidden = query !== "" && !word.dataset.search.includes(query);
  });
});

function appendEmphasis(parent, text) {
  text.split("*").forEach((part, index) => {
    if (!part) return;
    if (index % 2) {
      const em = document.createElement("em");
      em.textContent = part;
      parent.append(em);
    } else {
      parent.append(part);
    }
  });
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function shuffled(items) {
  return items
    .map((value) => [Math.random(), value])
    .sort((a, b) => a[0] - b[0])
    .map((pair) => pair[1]);
}

function canonical(text) {
  return text
    .toLowerCase()
    .replace(/\([^)]*\)/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^to /, "");
}

let quizKeys = null;

function initQuiz() {
  if (quizKeys) {
    document.removeEventListener("keydown", quizKeys);
    quizKeys = null;
  }

  const root = document.querySelector("[data-quiz]");
  const source = document.getElementById("quiz-data");
  if (!root || !source) return;

  const words = JSON.parse(source.textContent);
  if (!words.length) {
    root.textContent = "В словаре пока нет слов для диктанта.";
    return;
  }

  let questions = [];
  let position = 0;
  let score = 0;
  let missed = [];
  let answered = false;
  let form = null;
  let nextButton = null;

  function newRound() {
    questions = shuffled(words);
    position = 0;
    score = 0;
    missed = [];
    renderQuestion();
  }

  function renderQuestion() {
    const word = questions[position];
    answered = false;
    root.replaceChildren();

    const progress = element("div", "quiz-progress", `Вопрос ${position + 1} из ${questions.length}`);
    const bar = element("div", "quiz-bar");
    const fill = element("div", "quiz-bar__fill");
    fill.style.width = `${(position / questions.length) * 100}%`;
    bar.append(fill);

    const card = element("div", "quiz-card");
    card.append(element("div", "quiz-label", "Какое это слово?"));
    const list = element("ol", "quiz-definitions");
    word.definitions.forEach((definition) => {
      list.append(element("li", "", definition));
    });
    card.append(list);

    form = element("form", "quiz-form");
    const input = element("input", "quiz-input");
    input.type = "text";
    input.placeholder = "Введите слово по-английски";
    input.autocomplete = "off";
    input.spellcheck = false;
    input.setAttribute("autocapitalize", "off");
    input.setAttribute("aria-label", "Ответ");

    const check = element("button", "quiz-next", "Проверить");
    check.type = "submit";
    const skip = element("button", "quiz-skip", "Не знаю");
    skip.type = "button";
    skip.addEventListener("click", () => submit(input, "", true));
    form.append(input, check, skip);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      submit(input, input.value, false);
    });

    const feedback = element("div", "quiz-feedback");
    feedback.setAttribute("aria-live", "polite");

    nextButton = element("button", "quiz-next", position + 1 < questions.length ? "Дальше →" : "Результат");
    nextButton.type = "button";
    nextButton.hidden = true;
    nextButton.addEventListener("click", next);

    root.append(progress, bar, card, form, feedback, nextButton);
    input.focus({ preventScroll: true });
  }

  function submit(input, value, skipped) {
    if (answered) return;
    if (!skipped && !value.trim()) return;
    answered = true;

    const word = questions[position];
    const correct = !skipped && canonical(value) === canonical(word.word);
    if (correct) score += 1;
    else missed.push(word);

    input.disabled = true;
    input.classList.add(correct ? "quiz-input--correct" : "quiz-input--wrong");
    form.querySelectorAll("button").forEach((button) => {
      button.hidden = true;
    });

    const feedback = root.querySelector(".quiz-feedback");
    feedback.className = "quiz-feedback " + (correct ? "quiz-feedback--ok" : "quiz-feedback--bad");
    feedback.replaceChildren(
      element("strong", "", correct ? "Верно!" : `Правильный ответ: ${word.word}`),
    );
    if (!correct && !skipped) {
      feedback.append(element("p", "quiz-typed", `Вы ввели: ${value.trim()}`));
    }
    feedback.append(element("p", "quiz-sentence", word.sentence));
    feedback.append(element("p", "quiz-translation", word.translation));

    nextButton.hidden = false;
    nextButton.focus();
  }

  function next() {
    if (!answered) return;
    position += 1;
    if (position < questions.length) renderQuestion();
    else renderResult();
  }

  function renderResult() {
    root.replaceChildren();
    answered = false;
    nextButton = null;

    const percent = Math.round((score / questions.length) * 100);
    const card = element("div", "quiz-card quiz-result");
    card.append(element("div", "quiz-label", "Результат"));
    card.append(element("div", "quiz-score", `${score} из ${questions.length}`));
    card.append(element("div", "quiz-percent", `${percent}%`));

    if (missed.length) {
      card.append(element("div", "quiz-label quiz-label--spaced", "Повторить"));
      const list = element("div", "chips");
      missed.forEach((word) => {
        const chip = element("a", "chip", word.word);
        chip.href = (root.dataset.root || "") + word.url;
        list.append(chip);
      });
      card.append(list);
    } else {
      card.append(element("p", "", "Без ошибок!"));
    }

    const again = element("button", "quiz-next", "Новый диктант");
    again.type = "button";
    again.addEventListener("click", newRound);
    root.append(card, again);
  }

  quizKeys = (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (!answered) return;

    const target = eventElement(event);
    if (target.closest("input, textarea, select")) return;

    if (event.key === "ArrowRight") {
      next();
    } else if ([" ", "Enter"].includes(event.key) && !target.closest("button, a")) {
      next();
    } else {
      return;
    }

    event.preventDefault();
  };
  document.addEventListener("keydown", quizKeys);

  newRound();
}

if (typeof document$ !== "undefined") {
  document$.subscribe(initQuiz);
} else {
  document.addEventListener("DOMContentLoaded", initQuiz);
}
