// Animações da landing. Sem JS (ou com movimento reduzido) tudo aparece estático.
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var wait = function (ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  };

  // Seções entram ao rolar.
  var reveals = document.querySelectorAll(".reveal");
  if (reduced || !("IntersectionObserver" in window)) {
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  } else {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -10% 0px" });
    reveals.forEach(function (el) { observer.observe(el); });
  }

  if (reduced) return;

  // Conversa do celular: mensagens em sequência, com "digitando" antes do agente.
  var chat = document.querySelector("[data-chat]");
  var status = document.querySelector("[data-status]");
  if (chat) {
    var typing = chat.querySelector(".typing");
    var items = Array.prototype.filter.call(chat.children, function (li) { return li !== typing; });

    var play = async function () {
      for (;;) {
        items.forEach(function (li) { li.classList.remove("is-shown"); });
        chat.classList.add("is-playing");
        await wait(700);
        for (var i = 0; i < items.length; i++) {
          var li = items[i];
          if (li.classList.contains("bot")) {
            chat.appendChild(typing);
            typing.classList.add("is-shown");
            status.textContent = "digitando…";
            await wait(1300);
            typing.classList.remove("is-shown");
            status.textContent = "online";
          }
          chat.insertBefore(li, typing);
          li.classList.add("is-shown");
          await wait(li.classList.contains("route") ? 900 : 1100);
        }
        await wait(4500);
      }
    };
    play();
  }

  // Passo 2: as perguntas se revezam.
  var questions = document.querySelectorAll("[data-questions] li");
  if (questions.length) {
    var at = 0;
    setInterval(function () {
      at = (at + 1) % questions.length;
      questions.forEach(function (li, i) { li.classList.toggle("on", i === at); });
    }, 2000);
  }

  // Memória: sugestões chegam pendentes; só depois da verificação viram "verificada".
  var feed = document.querySelector("[data-feed]");
  if (feed) {
    var suggestions = [
      ["B", "Bia", "Vacina da gripe também aos sábados", true],
      ["T", "Téo", "Elevador da unidade em manutenção", false],
      ["N", "Nina", "Marcação de consulta pelo app da prefeitura", true],
      ["D", "Davi", "Nova sala de vacinação no 2º andar", true],
      ["I", "Iara", "Horário estendido às quintas", false]
    ];
    var next = 0;
    setInterval(function () {
      var item = suggestions[next];
      next = (next + 1) % suggestions.length;
      var li = document.createElement("li");
      li.className = "is-new";
      li.innerHTML = '<span class="ini"></span><span class="txt"><strong></strong><span></span></span><span class="state">pendente</span>';
      li.querySelector(".ini").textContent = item[0];
      li.querySelector("strong").textContent = item[1];
      li.querySelector(".txt span").textContent = item[2];
      feed.insertBefore(li, feed.firstChild);
      while (feed.children.length > 3) feed.removeChild(feed.lastChild);
      if (item[3]) {
        setTimeout(function () {
          var state = li.querySelector(".state");
          state.classList.add("ok");
          state.textContent = "verificada";
        }, 1800);
      }
    }, 3200);
  }
})();
