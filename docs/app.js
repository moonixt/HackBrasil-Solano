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

  // Passo 2: cada estado acende a sua região.
  var pills = document.querySelectorAll(".pills li");
  var from = document.querySelector(".mock-route .from");
  if (pills.length && from) {
    var states = ["PR", "SP", "GO", "AM", "BA"];
    var at = 0;
    setInterval(function () {
      at = (at + 1) % states.length;
      from.textContent = states[at];
      pills.forEach(function (li, i) { li.classList.toggle("on", i === at); });
    }, 2000);
  }

  // Memória: novas contribuições chegam no topo e o contador sobe.
  var feed = document.querySelector("[data-feed]");
  var count = document.querySelector("[data-count]");
  if (feed && count) {
    var contributions = [
      ["B", "Bia", "avisou que a linha de ônibus mudou"],
      ["T", "Téo", "indicou uma biblioteca aberta à noite"],
      ["N", "Nina", "contou onde tem feira aos domingos"],
      ["D", "Davi", "avisou de rua alagada na chuva"],
      ["I", "Iara", "indicou um posto que abre às 7h"],
      ["R", "Rafa", "contou sobre a feira do bairro"]
    ];
    var next = 0;
    setInterval(function () {
      var c = contributions[next];
      next = (next + 1) % contributions.length;
      var li = document.createElement("li");
      li.className = "is-new";
      li.innerHTML = '<span class="ini"></span><span><strong></strong> </span>';
      li.querySelector(".ini").textContent = c[0];
      li.querySelector("strong").textContent = c[1];
      li.lastChild.appendChild(document.createTextNode(c[2]));
      feed.insertBefore(li, feed.firstChild);
      while (feed.children.length > 3) feed.removeChild(feed.lastChild);
      count.textContent = String(Number(count.textContent) + 1);
    }, 2800);
  }
})();
