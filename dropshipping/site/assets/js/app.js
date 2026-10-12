/* Canapoil — script unique du site (aucune dépendance).
   Panier en localStorage, tiroir accessible, sélecteur d'offres, barre d'achat
   collante, dates de livraison en jours ouvrés, consentement aux traceurs,
   commande (démo ou Stripe), rétractation en ligne et inscriptions. */
(() => {
  "use strict";

  const CFG = window.CANAPOIL_CONFIG || {};
  const DEMO = CFG.mode !== "production";
  const PHASE = CFG.phase || "vente";
  const API = Object.assign({ checkout: "/api/create-checkout", retractation: "/api/retractation", inscription: "/api/inscription" }, CFG.api);
  const $ = (s, c) => (c || document).querySelector(s);
  const $$ = (s, c) => Array.from((c || document).querySelectorAll(s));
  const FMT = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR" });
  const FMT0 = new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", minimumFractionDigits: 0 });
  const euros = (c) => (c % 100 === 0 ? FMT0 : FMT).format(c / 100);
  const cents = (v) => Math.round(v * 100);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const ic = (n) => `<svg class="icone" aria-hidden="true" focusable="false"><use href="#i-${n}"/></svg>`;
  const PAGE = document.body.dataset.page || "";
  const CLE_PANIER = "canapoil_panier_v1";
  const CLE_CONSENT = "canapoil_consentement_v1";
  const CLE_CMD = "canapoil_derniere_commande";
  const JOUR = 864e5;
  const CGV_VERSION = "2026-10-12";

  const store = {
    get(k, s) { try { const v = (s ? sessionStorage : localStorage).getItem(k); return v ? JSON.parse(v) : null; } catch (e) { return null; } },
    set(k, v, s) { try { (s ? sessionStorage : localStorage).setItem(k, JSON.stringify(v)); } catch (e) { /* stockage indisponible */ } },
    del(k, s) { try { (s ? sessionStorage : localStorage).removeItem(k); } catch (e) { /* idem */ } },
  };

  let CAT = null;
  let IDX = {};
  let QMAX = 10;

  /* ------------------------------------------------------------ dates */
  function paques(a) {
    const b = a % 19, c = Math.floor(a / 100), d = a % 100, e = Math.floor(c / 4), f = c % 4,
      g = Math.floor((c + 8) / 25), h = Math.floor((c - g + 1) / 3), i = (19 * b + c - e - h + 15) % 30,
      k = Math.floor(d / 4), l = d % 4, m = (32 + 2 * f + 2 * k - i - l) % 7, n = Math.floor((b + 11 * i + 22 * m) / 451),
      mois = Math.floor((i + m - 7 * n + 114) / 31), jour = ((i + m - 7 * n + 114) % 31) + 1;
    return new Date(a, mois - 1, jour);
  }
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const feries = {};
  function estFerie(d) {
    const a = d.getFullYear();
    if (!feries[a]) {
      const p = paques(a), plus = (n) => iso(new Date(p.getFullYear(), p.getMonth(), p.getDate() + n));
      feries[a] = new Set(["01-01", "05-01", "05-08", "07-14", "08-15", "11-01", "11-11", "12-25"].map((x) => `${a}-${x}`).concat([plus(1), plus(39), plus(50)]));
    }
    return feries[a].has(iso(d));
  }
  const ouvre = (d) => d.getDay() !== 0 && d.getDay() !== 6 && !estFerie(d);
  function plusJoursOuvres(depart, n) {
    const d = new Date(depart.getFullYear(), depart.getMonth(), depart.getDate());
    let c = 0;
    while (c < n) { d.setDate(d.getDate() + 1); if (ouvre(d)) c++; }
    return d;
  }
  const FDATE = new Intl.DateTimeFormat("fr-FR", { weekday: "short", day: "numeric", month: "short" });
  const FDATE_LONG = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "long", year: "numeric" });
  function fourchette() {
    if (!CAT) return null;
    const L = CAT.livraison, c = CFG.livraison || {};
    const min = c.delai_min || L.delai_min_jours_ouvres, max = c.delai_max || L.delai_max_jours_ouvres;
    const auj = new Date();
    return { min, max, du: plusJoursOuvres(auj, min), au: plusJoursOuvres(auj, max) };
  }
  const dateIso = (s) => { const [a, m, j] = String(s).split("-").map(Number); return new Date(a, m - 1, j); };

  /* ------------------------------------------------------------ disponibilité */
  function enSaison(it, d) {
    d = d || new Date();
    if (it.disponible_jusqu_au && d > new Date(dateIso(it.disponible_jusqu_au).getTime() + JOUR)) return false;
    if (!it.saison) return true;
    const m = d.getMonth() + 1, s = it.saison;
    return s.debut_mois <= s.fin_mois ? m >= s.debut_mois && m <= s.fin_mois : m >= s.debut_mois || m <= s.fin_mois;
  }
  function disponible(it) {
    if (!it || PHASE === "liste_attente") return false;
    if (!enSaison(it)) return false;
    if (it.type === "kit") return it.composition.every((c) => enSaison(IDX[c.id] || {}));
    return true;
  }

  /* ------------------------------------------------------------ panier */
  function lirePanier() {
    const p = store.get(CLE_PANIER);
    if (!p || !Array.isArray(p.lignes) || Date.now() - (p.maj || 0) > 30 * JOUR) return [];
    return p.lignes
      .filter((l) => l && (!CAT || IDX[l.id]) && Number.isInteger(l.qte) && l.qte > 0)
      .map((l) => ({ id: l.id, qte: Math.min(l.qte, QMAX) }));
  }
  function ecrirePanier(lignes) {
    store.set(CLE_PANIER, { lignes, maj: Date.now() });
    majCompteur(lignes);
  }
  function ajouter(id, qte) {
    const it = IDX[id];
    if (!disponible(it)) return false;
    const lignes = lirePanier();
    const l = lignes.find((x) => x.id === id);
    if (l) l.qte = Math.min(QMAX, l.qte + qte); else lignes.push({ id, qte: Math.min(QMAX, qte) });
    ecrirePanier(lignes);
    return true;
  }
  function modifier(id, qte) {
    let lignes = lirePanier();
    if (qte <= 0) lignes = lignes.filter((x) => x.id !== id);
    else lignes.forEach((x) => { if (x.id === id) x.qte = Math.min(QMAX, qte); });
    ecrirePanier(lignes);
  }
  function remplacer(ids, kitId) {
    const lignes = lirePanier().filter((l) => !ids.includes(l.id));
    lignes.push({ id: kitId, qte: 1 });
    ecrirePanier(lignes);
  }
  function totaux(lignes) {
    const L = CAT.livraison;
    let sous = 0, nb = 0, offerteKit = false;
    lignes.forEach((l) => { const it = IDX[l.id]; sous += cents(it.prix_ttc) * l.qte; nb += l.qte; if (it.livraison_offerte) offerteKit = true; });
    const seuil = cents(L.seuil_gratuite_ttc);
    const offerte = nb > 0 && (offerteKit || sous >= seuil);
    const livraison = nb === 0 || offerte ? 0 : cents(L.frais_ttc);
    return { sous, nb, offerte, livraison, total: sous + livraison, manque: Math.max(0, seuil - sous), seuil };
  }
  function majCompteur(lignes) {
    const nb = (lignes || lirePanier()).reduce((s, l) => s + l.qte, 0);
    $$(".js-compteur").forEach((el) => { el.textContent = nb; el.dataset.vide = nb ? "false" : "true"; });
    $$(".js-ouvrir-panier").forEach((a) => a.setAttribute("aria-label", nb ? `Panier, ${nb} article${nb > 1 ? "s" : ""}` : "Panier vide"));
  }

  /* ------------------------------------------------------------ rendu du panier */
  function composition(it) {
    if (it.type !== "kit") return "";
    return it.composition.map((c) => (c.quantite > 1 ? c.quantite + " × " : "") + IDX[c.id].nom_court.replace(/^(Le|La) /, "")).join(" + ");
  }
  function htmlLignes(lignes, lecture) {
    if (!lignes.length) {
      return `<li class="vide"><p>Votre panier est vide.</p><a class="btn btn--primaire" href="/boutique/">Voir la boutique</a></li>`;
    }
    return lignes.map((l) => {
      const it = IDX[l.id], im = it.images[0], dispo = disponible(it);
      const actions = lecture
        ? `<div class="ligne__detail">Quantité : ${l.qte} × ${euros(cents(it.prix_ttc))}</div>`
        : `<div class="ligne__actions"><div class="quantite quantite--petite"><button type="button" data-action="moins" aria-label="Diminuer la quantité : ${esc(it.nom)}">−</button><input type="number" inputmode="numeric" min="1" max="${QMAX}" value="${l.qte}" data-action="qte" aria-label="Quantité : ${esc(it.nom)}"><button type="button" data-action="plus" aria-label="Augmenter la quantité : ${esc(it.nom)}">+</button></div><button type="button" class="btn-lien ligne__retirer" data-action="retirer">Retirer<span class="visuellement-cache"> ${esc(it.nom)}</span></button></div>`;
      return `<li class="ligne" data-id="${esc(it.id)}"><a class="ligne__visuel" href="${it.url}" tabindex="-1" aria-hidden="true"><img src="${im.src}" alt="" width="72" height="54"></a><div><p class="ligne__nom"><a href="${it.url}">${esc(it.nom)}</a></p>${it.type === "kit" ? `<p class="ligne__detail">${esc(composition(it))}${it.livraison_offerte ? " · livraison offerte" : ""}</p>` : ""}${dispo ? "" : '<p class="erreur">Indisponible actuellement : retirez-le pour commander.</p>'}${actions}</div><p class="ligne__prix">${euros(cents(it.prix_ttc) * l.qte)}</p></li>`;
    }).join("");
  }
  function htmlRecap(t) {
    const tva = CFG.tva === "franchise" ? "TVA non applicable, art. 293 B du CGI." : `Prix TTC, dont TVA 20 % : ${euros(Math.round(t.total - t.total / 1.2))}.`;
    return `<div class="recap__ligne"><span>Sous-total</span><span>${euros(t.sous)}</span></div>
      <div class="recap__ligne"><span>Livraison point relais</span><span>${t.nb === 0 ? "—" : t.offerte ? "Offerte" : euros(t.livraison)}</span></div>
      <div class="recap__ligne recap__ligne--total"><span>Total TTC</span><span>${euros(t.total)}</span></div>
      <p class="recap__note">${tva} Aucun frais à payer à la livraison.</p>`;
  }
  function majProgression(el, t) {
    if (!el) return;
    if (!t.nb) { el.innerHTML = ""; return; }
    const pct = t.offerte ? 100 : Math.min(100, Math.round((t.sous / t.seuil) * 100));
    const texte = t.offerte
      ? `${ic("check")} <strong>Livraison offerte</strong> pour cette commande.`
      : `Plus que <strong>${euros(t.manque)}</strong> pour la livraison offerte (dès ${euros(t.seuil)}).`;
    el.innerHTML = `<p class="progression__texte">${texte}</p><div class="progression__barre" role="progressbar" aria-label="Progression vers la livraison offerte" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct}"><span></span></div>`;
    const barre = $("span", $(".progression__barre", el));
    requestAnimationFrame(() => { barre.style.width = pct + "%"; });
  }
  function suggestion(lignes, t) {
    if (!lignes.length || PHASE === "liste_attente") return "";
    const ids = lignes.map((l) => l.id);
    // 1. Produits achetés séparément qui forment un kit moins cher : on le dit.
    for (const k of CAT.kits) {
      if (!disponible(k)) continue;
      const besoin = k.composition;
      if (besoin.every((c) => { const l = lignes.find((x) => x.id === c.id); return l && l.qte === c.quantite; })) {
        const avant = besoin.reduce((s, c) => s + cents(IDX[c.id].prix_ttc) * c.quantite, 0);
        return `<div class="suggestion"><img src="${k.images[0].src}" alt="" width="56" height="42"><p class="suggestion__texte">Ces produits existent en <strong>${esc(k.nom)}</strong> : ${euros(cents(k.prix_ttc))} au lieu de ${euros(avant)}${k.livraison_offerte ? ", livraison offerte" : ""}.</p><button type="button" class="btn btn--primaire" data-remplacer="${besoin.map((c) => c.id).join(",")}" data-kit="${k.id}">Remplacer</button></div>`;
      }
    }
    // 2. Rouleau seul : présenter le Grand kit avec l'écart réel.
    if (lignes.length === 1 && ids[0] === "rouleau-anti-poils" && lignes[0].qte === 1 && IDX["grand-kit"] && disponible(IDX["grand-kit"])) {
      const gk = IDX["grand-kit"], ecart = cents(gk.prix_ttc) - t.total;
      return `<div class="suggestion"><img src="${gk.images[0].src}" alt="" width="56" height="42"><p class="suggestion__texte">Le <strong>Grand kit</strong> ajoute la raclette (tapis, voiture) et le gant : ${euros(cents(gk.prix_ttc))}, livraison offerte, soit ${euros(ecart)} de plus que votre panier actuel.</p><button type="button" class="btn btn--primaire" data-remplacer="rouleau-anti-poils" data-kit="grand-kit">Choisir</button></div>`;
    }
    return "";
  }
  function rendrePaniers() {
    if (!CAT) return;
    const lignes = lirePanier(), t = totaux(lignes);
    $$(".js-lignes").forEach((ul) => { ul.innerHTML = htmlLignes(lignes, ul.classList.contains("js-lignes-lecture")); });
    $$(".js-recap").forEach((el) => { el.innerHTML = htmlRecap(t); });
    $$(".js-progression").forEach((el) => majProgression(el, t));
    $$(".js-suggestion").forEach((el) => { el.innerHTML = suggestion(lignes, t); });
    const bloque = !t.nb || lignes.some((l) => !disponible(IDX[l.id]));
    $$(".js-vers-commande").forEach((a) => {
      a.setAttribute("aria-disabled", bloque ? "true" : "false");
      if (bloque) a.removeAttribute("href"); else a.setAttribute("href", "/commande/");
    });
    majCompteur(lignes);
  }
  function surActionLigne(ev) {
    const cible = ev.target.closest("[data-action],[data-remplacer]");
    if (!cible) return;
    if (cible.dataset.remplacer) {
      remplacer(cible.dataset.remplacer.split(","), cible.dataset.kit);
      rendrePaniers();
      annoncer("Panier mis à jour");
      return;
    }
    const li = cible.closest(".ligne");
    if (!li) return;
    const id = li.dataset.id, l = lirePanier().find((x) => x.id === id);
    if (!l) return;
    const a = cible.dataset.action;
    if (ev.type === "change" && a === "qte") modifier(id, parseInt(cible.value, 10) || 0);
    else if (ev.type === "click" && a === "plus") modifier(id, l.qte + 1);
    else if (ev.type === "click" && a === "moins") modifier(id, l.qte - 1);
    else if (ev.type === "click" && a === "retirer") modifier(id, 0);
    else return;
    rendrePaniers();
    annoncer("Panier mis à jour");
    const meme = $(`.ligne[data-id="${id}"] [data-action="${a}"]`, ev.currentTarget);
    if (meme && ev.type === "click") meme.focus();
    else { const t = $(".tiroir.visible [data-fermer-panier]"); if (t && a === "retirer") t.focus(); }
  }

  let minuteur;
  function annoncer(txt) {
    const n = $(".js-notification");
    if (!n) return;
    n.textContent = txt;
    n.hidden = false;
    clearTimeout(minuteur);
    minuteur = setTimeout(() => { n.hidden = true; }, 2200);
  }

  /* ------------------------------------------------------------ tiroir */
  const tiroir = $("#tiroir-panier");
  const fond = $(".tiroir-fond");
  let focusAvant = null;
  function ouvrirTiroir() {
    if (!tiroir) return;
    focusAvant = document.activeElement;
    rendrePaniers();
    tiroir.hidden = false;
    fond.hidden = false;
    requestAnimationFrame(() => { tiroir.classList.add("visible"); fond.classList.add("visible"); });
    document.body.style.overflow = "hidden";
    const f = $("[data-fermer-panier]", tiroir);
    if (f) setTimeout(() => f.focus(), 30);
  }
  function fermerTiroir() {
    if (!tiroir || tiroir.hidden) return;
    tiroir.classList.remove("visible");
    fond.classList.remove("visible");
    document.body.style.overflow = "";
    setTimeout(() => { tiroir.hidden = true; fond.hidden = true; }, 260);
    if (focusAvant && focusAvant.focus) focusAvant.focus();
  }
  function pieger(ev) {
    if (ev.key === "Escape") { fermerTiroir(); return; }
    if (ev.key !== "Tab") return;
    const f = $$('a[href],button:not([disabled]),input,[tabindex="0"]', tiroir).filter((x) => x.offsetParent !== null);
    if (!f.length) return;
    const premier = f[0], dernier = f[f.length - 1];
    if (ev.shiftKey && document.activeElement === premier) { ev.preventDefault(); dernier.focus(); }
    else if (!ev.shiftKey && document.activeElement === dernier) { ev.preventDefault(); premier.focus(); }
  }

  function apresAjout() {
    if (PAGE === "panier" || PAGE === "commande") { rendrePaniers(); annoncer("Ajouté au panier"); }
    else ouvrirTiroir();
  }

  /* ------------------------------------------------------------ fiche produit */
  function initFiche() {
    const bloc = $(".js-achat");
    if (!bloc) return;
    const bouton = $(".js-ajouter", bloc);
    const qteInput = $(".js-quantite input", bloc);
    const upsell = $(".js-upsell input", bloc);
    const barre = $(".js-barre-achat");
    const offre = () => { const r = $('input[name="offre"]:checked', bloc) || $('input[name="offre"]', bloc); return r ? r.value : bloc.dataset.produit; };
    const qte = () => Math.min(QMAX, Math.max(1, parseInt(qteInput && qteInput.value, 10) || 1));

    if (PHASE === "liste_attente") {
      const tpl = $("#tpl-attente");
      if (tpl) { bloc.innerHTML = ""; bloc.appendChild(tpl.content.cloneNode(true)); initInscriptions(bloc); }
      if (barre) barre.remove();
      document.body.classList.remove("avec-barre");
      return;
    }

    function maj() {
      const it = IDX[offre()];
      if (!it) return;
      const ok = disponible(it), total = euros(cents(it.prix_ttc) * qte());
      $(".js-prix-bouton", bloc).textContent = total;
      $$(".js-prix-offre").forEach((el) => { el.textContent = euros(cents(it.prix_ttc)); });
      $(".js-libelle-ajout", bloc).textContent = ok ? (PHASE === "precommande" ? "Précommander" : "Ajouter au panier") : "Hors saison";
      bouton.disabled = !ok;
      if (upsell) {
        const v = offre();
        upsell.closest(".js-upsell").hidden = !(v === "rouleau-anti-poils" || v === "kit-anti-poils");
        upsell.checked = v === "kit-anti-poils";
      }
      if (barre) {
        $(".js-barre-nom", barre).textContent = it.nom + (qte() > 1 ? ` × ${qte()}` : "");
        $(".js-barre-prix", barre).textContent = total;
        const b = $(".js-barre-ajouter", barre);
        b.disabled = !ok;
        b.textContent = ok ? (PHASE === "precommande" ? "Précommander" : "Ajouter au panier") : "Hors saison";
      }
      $$(".offre", bloc).forEach((o) => { const x = IDX[o.dataset.offre]; o.dataset.indisponible = x && !disponible(x) ? "true" : "false"; });
    }
    if (upsell) {
      const gant = IDX["gant-toilettage"], kit = IDX["kit-anti-poils"], rouleau = IDX["rouleau-anti-poils"];
      const lib = upsell.closest(".js-upsell");
      const diff = cents(kit.prix_ttc) - cents(rouleau.prix_ttc);
      $("strong", lib).textContent = `Ajouter le gant de toilettage (+${euros(diff)})`;
      $(".texte-2", lib).textContent = `Rouleau + gant = Kit anti-poils à ${euros(cents(kit.prix_ttc))} au lieu de ${euros(cents(rouleau.prix_ttc) + cents(gant.prix_ttc))} séparément. Le gant récupère une partie des poils au brossage.`;
      upsell.addEventListener("change", () => {
        const cible = $(`input[name="offre"][value="${upsell.checked ? "kit-anti-poils" : "rouleau-anti-poils"}"]`, bloc);
        if (cible) cible.checked = true;
        maj();
      });
    }
    bloc.addEventListener("change", (ev) => { if (ev.target.name === "offre" || ev.target === qteInput) maj(); });
    $$(".js-quantite button", bloc).forEach((b) => b.addEventListener("click", () => {
      qteInput.value = Math.min(QMAX, Math.max(1, qte() + parseInt(b.dataset.pas, 10)));
      maj();
    }));
    if (qteInput) qteInput.addEventListener("input", maj);
    const ajout = () => { if (ajouter(offre(), qte())) apresAjout(); };
    bouton.addEventListener("click", ajout);
    if (barre) {
      $(".js-barre-ajouter", barre).addEventListener("click", ajout);
      if ("IntersectionObserver" in window) {
        new IntersectionObserver((entrees) => {
          entrees.forEach((en) => {
            const voir = !en.isIntersecting && en.boundingClientRect.top < 0;
            barre.classList.toggle("visible", voir);
            barre.setAttribute("aria-hidden", voir ? "false" : "true");
            $(".js-barre-ajouter", barre).tabIndex = voir ? 0 : -1;
          });
        }).observe(bouton);
      }
    }
    maj();
  }

  function initGaleries() {
    $$(".js-galerie").forEach((g) => {
      const piste = $(".galerie__principale", g), vign = $$(".galerie__vignettes button", g);
      if (!piste || !vign.length) return;
      vign.forEach((b) => b.addEventListener("click", () => {
        const i = parseInt(b.dataset.cible, 10);
        piste.scrollTo({ left: piste.clientWidth * i, behavior: "smooth" });
        vign.forEach((x) => x.setAttribute("aria-current", x === b ? "true" : "false"));
      }));
      let t;
      piste.addEventListener("scroll", () => {
        clearTimeout(t);
        t = setTimeout(() => {
          const i = Math.round(piste.scrollLeft / piste.clientWidth);
          vign.forEach((x, j) => x.setAttribute("aria-current", j === i ? "true" : "false"));
        }, 80);
      }, { passive: true });
    });
  }

  function initDates() {
    const f = fourchette();
    if (!f) return;
    const txt = `, soit entre le ${FDATE.format(f.du)} et le ${FDATE.format(f.au)} pour une commande passée aujourd'hui`;
    $$(".js-dates-livraison").forEach((el) => { el.textContent = PHASE === "vente" ? txt : ""; });
    if (PHASE === "precommande" && CFG.precommande) {
      const p = CFG.precommande, d1 = dateIso(p.expedition_a_partir_du), d2 = dateIso(p.livraison_au_plus_tard_le);
      $$(".js-precommande-texte").forEach((el) => {
        el.hidden = false;
        el.closest(".encart").classList.add("encart--precommande");
        $("span", el).innerHTML = `<strong>Précommande</strong> : expédition à partir du ${FDATE_LONG.format(d1)}, livraison au plus tard le ${FDATE_LONG.format(d2)}.${p.prime ? " " + esc(p.prime) + "." : ""}`;
      });
    }
  }

  function initCartes() {
    $$(".js-ajout-rapide").forEach((b) => {
      const it = IDX[b.dataset.ajouter];
      if (PHASE === "liste_attente") { b.hidden = true; return; }
      if (!disponible(it)) { b.disabled = true; b.textContent = "Hors saison"; return; }
      if (PHASE === "precommande") b.textContent = "Précommander";
      b.addEventListener("click", () => { if (ajouter(it.id, 1)) apresAjout(); });
    });
  }

  function hydraterPrix() {
    $$("[data-prix]").forEach((el) => { const it = IDX[el.dataset.prix]; if (it) el.textContent = euros(cents(it.prix_ttc)); });
  }

  /* ------------------------------------------------------------ commande */
  function numeroDemo() { return "DEMO-" + Math.random().toString(36).slice(2, 8).toUpperCase(); }

  async function posterJSON(url, donnees) {
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(donnees) });
    let corps = {};
    try { corps = await r.json(); } catch (e) { /* réponse vide */ }
    if (!r.ok) throw new Error(corps.erreur || "Le service est momentanément indisponible. Réessayez dans quelques minutes ou écrivez-nous.");
    return corps;
  }

  function initCommande() {
    const form = $(".js-form-commande");
    if (!form) return;
    $$(".js-avertissement-demo").forEach((el) => { el.hidden = !DEMO; });
    const erreur = $(".js-erreur-commande", form);
    const cgv = $("#cgv", form);
    const errCgv = $("#erreur-cgv");
    const bouton = $(".js-payer", form);
    if (PHASE === "liste_attente") {
      bouton.disabled = true;
      erreur.hidden = false;
      erreur.textContent = "Les ventes ne sont pas encore ouvertes. Inscrivez-vous sur une fiche produit pour être prévenu du lancement.";
      return;
    }
    cgv.addEventListener("change", () => { if (cgv.checked) { errCgv.textContent = ""; cgv.removeAttribute("aria-invalid"); } });
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      erreur.hidden = true;
      const lignes = lirePanier();
      if (!lignes.length) { erreur.hidden = false; erreur.innerHTML = 'Votre panier est vide. <a href="/boutique/">Voir la boutique</a>'; return; }
      if (lignes.some((l) => !disponible(IDX[l.id]))) { erreur.hidden = false; erreur.textContent = "Un article de votre panier est indisponible : retirez-le pour continuer."; return; }
      if (!cgv.checked) {
        errCgv.textContent = "Cochez la case pour accepter les conditions générales de vente.";
        cgv.setAttribute("aria-invalid", "true");
        cgv.focus();
        return;
      }
      const t = totaux(lignes);
      const relais = $("#point-relais", form).value.trim().slice(0, 80);
      const recap = {
        lignes, totaux: t, point_relais: relais, date: new Date().toISOString(), demo: DEMO, phase: PHASE,
      };
      bouton.disabled = true;
      bouton.textContent = DEMO ? "Simulation en cours…" : "Redirection vers Stripe…";
      if (DEMO) {
        recap.numero = numeroDemo();
        store.set(CLE_CMD, recap, true);
        setTimeout(() => { window.location.href = "/merci.html?demo=1"; }, 350);
        return;
      }
      try {
        const rep = await posterJSON(API.checkout, { lignes, point_relais: relais, cgv_acceptees: true, cgv_version: CGV_VERSION, phase: PHASE });
        if (!rep.url) throw new Error("Réponse inattendue du serveur de paiement.");
        store.set(CLE_CMD, recap, true);
        window.location.href = rep.url;
      } catch (e) {
        erreur.hidden = false;
        erreur.textContent = e.message;
        bouton.disabled = false;
        bouton.textContent = "Continuer vers le paiement sécurisé";
      }
    });
  }

  function initMerci() {
    if (PAGE !== "merci") return;
    const p = new URLSearchParams(window.location.search);
    const demo = p.has("demo"), paye = p.has("session_id");
    const cmd = store.get(CLE_CMD, true);
    $(".js-merci-demo").hidden = !demo;
    if (!demo && !paye) {
      $(".js-merci-titre").textContent = "Aucune commande en cours";
      $(".js-merci-chapo").textContent = "Cette page s'affiche après un paiement. Si vous venez de payer et ne recevez pas d'e-mail de confirmation, écrivez-nous.";
      return;
    }
    store.del(CLE_PANIER);
    majCompteur([]);
    if (demo) $(".js-merci-chapo").textContent = "En production, un e-mail de confirmation serait envoyé avec le récapitulatif, nos conditions générales de vente et le formulaire de rétractation.";
    if (cmd && CAT) {
      const lignes = cmd.lignes.filter((l) => IDX[l.id]);
      $(".js-merci-recap").hidden = false;
      $(".js-merci-numero").textContent = cmd.numero ? `Commande ${cmd.numero} (simulation)` : "Récapitulatif transmis à la page de paiement.";
      $(".js-merci-lignes").innerHTML = htmlLignes(lignes, true);
      $(".js-merci-totaux").innerHTML = htmlRecap(totaux(lignes)) + (cmd.point_relais ? `<p class="recap__note">Point relais demandé : ${esc(cmd.point_relais)}</p>` : "");
    }
  }

  /* ------------------------------------------------------------ formulaires */
  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

  function initInscriptions(racine) {
    $$(".js-form-inscription", racine).forEach((form) => {
      if (form.dataset.pret) return;
      form.dataset.pret = "1";
      form.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const champ = $('input[type="email"]', form), err = $(".js-erreur", form), email = champ.value.trim();
        err.textContent = "";
        champ.removeAttribute("aria-invalid");
        if (!EMAIL_RE.test(email)) { err.textContent = "Saisissez une adresse e-mail valide, par exemple nom@exemple.fr."; champ.setAttribute("aria-invalid", "true"); champ.focus(); return; }
        const b = $('button[type="submit"]', form);
        b.disabled = true;
        try {
          if (!DEMO) await posterJSON(API.inscription, { email, source: form.dataset.source || "site" });
          form.innerHTML = `<p class="message message--succes" role="status" tabindex="-1">${DEMO ? "Simulation : en production, un e-mail de confirmation serait envoyé à " + esc(email) + "." : "Merci ! Confirmez votre inscription grâce à l'e-mail envoyé à " + esc(email) + "."}</p>`;
          $(".message", form).focus();
        } catch (e) { err.textContent = e.message; b.disabled = false; }
      });
    });
  }

  function initRetractation() {
    const form = $(".js-form-retractation");
    if (!form) return;
    $$(".js-avertissement-demo").forEach((el) => { el.hidden = !DEMO; });
    const zone = $(".js-accuse"), erreurG = $(".js-erreur-retractation", form);
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      erreurG.hidden = true;
      let premier = null;
      const v = {};
      ["nom", "prenom", "commande", "email", "produits"].forEach((n) => {
        const c = form.elements[n], err = c.parentElement.querySelector(".erreur");
        v[n] = c.value.trim();
        if (!err) return;
        let msg = "";
        if (!v[n]) msg = "Ce champ est obligatoire.";
        else if (n === "email" && !EMAIL_RE.test(v[n])) msg = "Saisissez une adresse e-mail valide.";
        err.textContent = msg;
        if (msg) { c.setAttribute("aria-invalid", "true"); premier = premier || c; } else c.removeAttribute("aria-invalid");
      });
      if (premier) { premier.focus(); return; }
      const b = $('button[type="submit"]', form);
      b.disabled = true;
      let horodatage = new Date().toISOString(), reference = "";
      try {
        if (!DEMO) { const r = await posterJSON(API.retractation, v); horodatage = r.horodatage || horodatage; reference = r.reference || ""; }
      } catch (e) { erreurG.hidden = false; erreurG.textContent = e.message; b.disabled = false; return; }
      const quand = new Intl.DateTimeFormat("fr-FR", { dateStyle: "full", timeStyle: "medium", timeZone: "Europe/Paris" }).format(new Date(horodatage));
      zone.innerHTML = `<h2>Accusé de réception de votre rétractation</h2>
        ${DEMO ? '<p class="message message--demo"><strong>Simulation</strong> : en production, cet accusé est aussi envoyé par e-mail.</p>' : `<p class="message message--succes">Cet accusé vous a été envoyé par e-mail à ${esc(v.email)}.</p>`}
        <dl><dt>Envoyée le</dt><dd>${esc(quand)} (heure de Paris)</dd>${reference ? `<dt>Référence</dt><dd>${esc(reference)}</dd>` : ""}<dt>Nom</dt><dd>${esc(v.nom)}</dd><dt>Prénom</dt><dd>${esc(v.prenom)}</dd><dt>Commande</dt><dd>${esc(v.commande)}</dd><dt>E-mail</dt><dd>${esc(v.email)}</dd><dt>Produits</dt><dd>${v.produits ? esc(v.produits) : "Toute la commande"}</dd></dl>
        <p>Déclaration : « Je notifie par la présente ma rétractation du contrat portant sur la vente des biens ci-dessus. »</p>
        <p><button type="button" class="btn btn--secondaire js-imprimer">Imprimer ou enregistrer en PDF</button></p>`;
      zone.hidden = false;
      form.hidden = true;
      $(".js-imprimer", zone).addEventListener("click", () => window.print());
      zone.focus({ preventScroll: true });
      zone.scrollIntoView({ block: "start" });
    });
  }

  /* ------------------------------------------------------------ consentement */
  function lireConsent() {
    const c = store.get(CLE_CONSENT), duree = ((CFG.consentement || {}).duree_jours || 182) * JOUR;
    return c && Date.now() - c.date < duree ? c : null;
  }
  function chargerTraceurs(liste) {
    (liste || []).forEach((t) => {
      if (!t || !t.src || $(`script[data-traceur="${t.nom}"]`)) return;
      const s = document.createElement("script");
      s.src = t.src;
      s.async = true;
      s.dataset.traceur = t.nom || t.src;
      document.head.appendChild(s);
    });
  }
  function appliquerConsent(c) {
    const tr = CFG.traceurs || {};
    if (c.mesure) chargerTraceurs(tr.mesure);
    if (c.publicite) chargerTraceurs(tr.publicite);
  }
  function initCookies() {
    const b = $("#bandeau-cookies");
    if (!b) return;
    const choix = $(".js-cookies-choix", b), perso = $(".js-cookies-personnaliser", b), enr = $(".js-cookies-enregistrer", b);
    const actuel = lireConsent();
    if (actuel) appliquerConsent(actuel); else b.hidden = false;
    const enregistrer = (c) => {
      const avant = lireConsent();
      store.set(CLE_CONSENT, { mesure: !!c.mesure, publicite: !!c.publicite, date: Date.now(), version: 1 });
      b.hidden = true;
      if (avant && ((avant.mesure && !c.mesure) || (avant.publicite && !c.publicite))) { window.location.reload(); return; }
      appliquerConsent(c);
    };
    $(".js-cookies-refuser", b).addEventListener("click", () => enregistrer({ mesure: false, publicite: false }));
    $(".js-cookies-accepter", b).addEventListener("click", () => enregistrer({ mesure: true, publicite: true }));
    const montrerChoix = () => {
      const c = lireConsent() || {};
      choix.hidden = false; perso.hidden = true; enr.hidden = false;
      choix.querySelector('[name="mesure"]').checked = !!c.mesure;
      choix.querySelector('[name="publicite"]').checked = !!c.publicite;
    };
    perso.addEventListener("click", () => { montrerChoix(); choix.querySelector("input").focus(); });
    enr.addEventListener("click", () => enregistrer({ mesure: choix.querySelector('[name="mesure"]').checked, publicite: choix.querySelector('[name="publicite"]').checked }));
    $$(".js-gerer-cookies").forEach((g) => g.addEventListener("click", () => { b.hidden = false; montrerChoix(); $(".js-cookies-refuser", b).focus(); }));
  }

  /* ------------------------------------------------------------ divers */
  function initMenu() {
    const btn = $(".js-menu"), entete = $(".entete");
    if (!btn) return;
    const basculer = (ouvert) => {
      entete.classList.toggle("menu-ouvert", ouvert);
      btn.setAttribute("aria-expanded", ouvert ? "true" : "false");
      btn.setAttribute("aria-label", ouvert ? "Fermer le menu" : "Ouvrir le menu");
    };
    btn.addEventListener("click", () => basculer(!entete.classList.contains("menu-ouvert")));
    document.addEventListener("keydown", (ev) => { if (ev.key === "Escape" && entete.classList.contains("menu-ouvert")) { basculer(false); btn.focus(); } });
  }
  function initReseaux() {
    const r = CFG.reseaux || {};
    const liens = Object.keys(r).filter((k) => /^https:\/\//.test(r[k] || "")).map((k) => `<a href="${esc(r[k])}" rel="noopener">${esc(k)}</a>`);
    $$(".js-reseaux").forEach((el) => { el.innerHTML = liens.join(""); el.hidden = !liens.length; });
  }
  function initPhase() {
    if (PHASE !== "liste_attente") return;
    $$(".js-ouvrir-panier").forEach((a) => { a.hidden = true; });
  }

  /* ------------------------------------------------------------ démarrage */
  function demarrer() {
    initMenu();
    initCookies();
    initReseaux();
    initPhase();
    initInscriptions(document);
    initRetractation();
    initGaleries();
    majCompteur(lirePanier());
    $$(".js-ouvrir-panier").forEach((a) => a.addEventListener("click", (ev) => {
      if (PAGE === "panier" || PAGE === "commande") return;
      ev.preventDefault();
      ouvrirTiroir();
    }));
    $$("[data-fermer-panier]").forEach((x) => x.addEventListener("click", fermerTiroir));
    if (tiroir) tiroir.addEventListener("keydown", pieger);
    $$(".js-lignes, .js-suggestion").forEach((el) => {
      el.addEventListener("click", surActionLigne);
      el.addEventListener("change", surActionLigne);
    });
    $$(".js-vers-commande").forEach((a) => a.addEventListener("click", (ev) => { if (a.getAttribute("aria-disabled") === "true") ev.preventDefault(); }));

    fetch("/data/products.json", { cache: "no-cache" })
      .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then((cat) => {
        CAT = cat;
        QMAX = cat.quantite_max_par_ligne || 10;
        cat.produits.concat(cat.kits).forEach((x) => { IDX[x.id] = x; });
        majCompteur(lirePanier());
        hydraterPrix();
        initDates();
        initFiche();
        initCartes();
        initCommande();
        rendrePaniers();
        initMerci();
        window.addEventListener("storage", (ev) => { if (ev.key === CLE_PANIER) rendrePaniers(); });
      })
      .catch(() => {
        $$(".js-lignes").forEach((ul) => { ul.innerHTML = '<li class="message message--alerte">Le catalogue n\'a pas pu être chargé. Rechargez la page.</li>'; });
        $$(".js-ajouter, .js-ajout-rapide, .js-payer").forEach((b) => { b.disabled = true; });
      });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", demarrer);
  else demarrer();
})();
