# Audit de Securite - CRM Ma Boite Immo

**Date** : 18 mars 2026
**Cible** : https://ma-boite-immo.com / https://api.ma-boite-immo.com
**Type** : Analyse externe (black-box) depuis la page de connexion et le bundle JS

---

## Resume des Vulnerabilites

| # | Vulnerabilite | Severite | OWASP |
|---|--------------|----------|-------|
| 1 | Documentation API exposee publiquement | **CRITIQUE** | A01 - Broken Access Control |
| 2 | DSN Sentry expose dans le bundle JS | **HAUTE** | A05 - Security Misconfiguration |
| 3 | Headers de securite manquants | **HAUTE** | A05 - Security Misconfiguration |
| 4 | Cookie sans flags de securite | **HAUTE** | A07 - Identification & Auth Failures |
| 5 | Version serveur exposee (nginx/1.27.3) | **MOYENNE** | A05 - Security Misconfiguration |
| 6 | Source maps potentiellement accessibles | **MOYENNE** | A05 - Security Misconfiguration |
| 7 | Endpoints API sensibles exposes | **HAUTE** | A01 - Broken Access Control |
| 8 | Pas de protection CSRF visible | **MOYENNE** | A01 - Broken Access Control |
| 9 | Informations d'architecture exposees | **MOYENNE** | A05 - Security Misconfiguration |
| 10 | Pas de rate limiting apparent sur /auth | **HAUTE** | A07 - Identification & Auth Failures |

---

## Detail des Vulnerabilites

### 1. CRITIQUE - Documentation API Hydra exposee publiquement

**Endpoint** : `https://api.ma-boite-immo.com/docs`

La documentation complete de l'API (format JSON-LD / Hydra) est accessible **sans authentification**.
Elle expose :

- **Toutes les entites metier** : `Account`, `User`, `Client`, `Licence`, `Article`, `Address`, `AppProduct`, `Subscription`, `BillingEntitiesUsersAuthorizations`, etc.
- **Toutes les operations CRUD** : GET, PUT, PATCH, DELETE sur des ressources sensibles
- **La structure des donnees** : champs, types, relations entre entites
- **Les endpoints d'administration** : gestion des licences, produits, utilisateurs

Cela donne a un attaquant une cartographie complete de l'API pour preparer des attaques ciblees.

**Remediation** :
- Desactiver l'acces public a `/docs` en production
- Restreindre via authentification ou IP whitelist
- Configurer dans API Platform : `enable_docs: false` en production

---

### 2. HAUTE - DSN Sentry expose dans le bundle JavaScript

**Valeur exposee** :
```
dsn: "https://7dc65be6fa7f4a16a6a3f021fc810bb4@o4504197474484224.ingest.sentry.io/4504197480513536"
```

Le DSN Sentry est en clair dans le bundle JS. Un attaquant peut :
- Envoyer de faux rapports d'erreur pour polluer votre monitoring
- Potentiellement extraire des informations sur les erreurs via l'API Sentry
- Identifier l'organisation Sentry (ID: `4504197474484224`, projet: `4504197480513536`)

**Remediation** :
- Configurer le `allowedDomains` dans Sentry pour n'accepter que `ma-boite-immo.com`
- Utiliser les Sentry Security Headers (rate limiting cote Sentry)
- Envisager un tunnel Sentry backend pour ne pas exposer le DSN

---

### 3. HAUTE - Headers de securite HTTP manquants

**Headers presents** :
- `Strict-Transport-Security` : OK (max-age=16000000, includeSubDomains, preload)

**Headers MANQUANTS** :
- `Content-Security-Policy` (CSP) : **Absent** - Pas de protection contre XSS/injection de scripts
- `X-Frame-Options` : **Absent** - Vulnerable au clickjacking
- `X-Content-Type-Options` : **Absent** - Vulnerable au MIME sniffing
- `X-XSS-Protection` : **Absent**
- `Referrer-Policy` : **Absent** - Fuite potentielle d'URLs dans le header Referer
- `Permissions-Policy` : **Absent** - Pas de restriction sur les API du navigateur

**Remediation** :
```nginx
# Ajouter dans la configuration nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://api.ma-boite-immo.com https://o4504197474484224.ingest.sentry.io;";
add_header X-Frame-Options "DENY";
add_header X-Content-Type-Options "nosniff";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()";
```

---

### 4. HAUTE - Cookie sans flags de securite

**Cookie observe** :
```
Set-Cookie: SERVERUSED=mbi2; path=/
```

Le cookie `SERVERUSED` (qui revele le serveur backend utilise) est defini **sans** :
- `Secure` : Le cookie pourrait etre envoye en clair sur HTTP
- `HttpOnly` : Le cookie est accessible via JavaScript (vol possible via XSS)
- `SameSite` : Pas de protection contre les attaques CSRF

De plus, le nom `SERVERUSED=mbi1/mbi2/mbi3/mbi4` **revele l'infrastructure interne** (load balancing entre 4+ serveurs nommes mbi1 a mbi4).

**Remediation** :
```nginx
proxy_cookie_flags SERVERUSED secure httponly samesite=strict;
```
Ou mieux : supprimer ce cookie cote client s'il n'est utile que pour le load balancer.

---

### 5. MOYENNE - Version serveur exposee

```
server: nginx/1.27.3
```

La version exacte de nginx est exposee, ce qui permet a un attaquant de chercher des CVE specifiques.

**Remediation** :
```nginx
server_tokens off;
```

---

### 6. MOYENNE - Source maps potentiellement accessibles

La requete vers `index-CezqpEvY.js.map` retourne un HTTP 200 avec le HTML de la SPA (fallback nginx).
Cela signifie que nginx ne bloque pas explicitement les fichiers `.map`.
Si des source maps existent, elles exposeraient le code source original non-minifie.

**Remediation** :
```nginx
location ~* \.map$ {
    return 404;
}
```

---

### 7. HAUTE - Endpoints API sensibles exposes dans le bundle JS

Le bundle JavaScript revele l'ensemble des routes API :

**Routes sensibles identifiees** :
- `/auth` - Endpoint d'authentification (POST email/password en clair dans le body)
- `/forgot_password` - Reset de mot de passe
- `/accounts` - Gestion des comptes
- `/client_admin` - Administration client
- `/leads` - Donnees prospects
- `/orders` - Commandes
- `/customer_space` - Espace client
- `/logical_entities_users` - Gestion des utilisateurs/entites
- `/app_product_user_accesses` - Gestion des acces utilisateur

**Operations CRUD completes** (PUT/DELETE) exposees sur :
`Address`, `AppProduct`, `AppProductUserAccess`, `Article`, `User`, `BillingEntitiesUsersAuthorizations`...

**Remediation** :
- Verifier que chaque endpoint applique une verification d'autorisation stricte (RBAC)
- Implementer une validation cote serveur sur tous les endpoints destructifs (DELETE, PUT)
- Auditer les permissions : un negotiator ne devrait pas pouvoir acceder aux endpoints admin

---

### 8. MOYENNE - Pas de protection CSRF visible

L'authentification se fait via JWT Bearer token (`Authorization: Bearer ${token}`).
Cependant :
- Aucun token CSRF n'est visible dans le formulaire de login
- Les cookies n'ont pas le flag `SameSite`
- Si le JWT est stocke dans un cookie (et non localStorage), des attaques CSRF sont possibles

**Remediation** :
- S'assurer que le JWT est stocke en `localStorage` ou `sessionStorage` (pas dans un cookie)
- Ajouter `SameSite=Strict` sur tous les cookies
- Implementer un token CSRF pour les actions sensibles

---

### 9. MOYENNE - Fuites d'informations sur l'architecture

Le bundle JS et les headers revelent :
- **Framework frontend** : React (SPA avec Vite)
- **UI** : Material UI (MUI)
- **State management** : Redux Toolkit
- **HTTP client** : Axios
- **Backend** : API Platform (Symfony/PHP) via Hydra JSON-LD
- **Proxy** : Envoy + Caddy
- **Serveur** : nginx/1.27.3
- **Monitoring** : Sentry (org ID + project ID)
- **Analytics** : Google Tag Manager
- **Tracking IP** : api.ipify.org
- **Roles utilisateurs** : `network_manager`, `agency_manager`, `negotiator`, `secretary`, `agent`

Cette cartographie complete facilite grandement la preparation d'attaques ciblees.

---

### 10. HAUTE - Pas de rate limiting apparent sur l'endpoint d'authentification

L'endpoint `POST /auth` accepte les requetes sans mecanisme visible de rate limiting.
Cela expose a :
- **Brute force** sur les mots de passe
- **Credential stuffing** (essai de credentials fuites)
- **Enumeration de comptes** (si les messages d'erreur different entre "compte inexistant" et "mauvais mot de passe")

Le message d'erreur generique "Invalid credentials." est un bon point, mais insuffisant sans rate limiting.

**Remediation** :
- Implementer un rate limiting sur `/auth` (ex: 5 tentatives / 15 min par IP)
- Ajouter un captcha apres N echecs
- Implementer un delai progressif (exponential backoff)
- Monitorer les tentatives echouees dans Sentry/logs

---

## Recommandations Prioritaires

### Immediat (cette semaine)
1. **Desactiver `/docs`** sur l'API en production
2. **Ajouter les headers de securite** manquants dans nginx
3. **Securiser les cookies** (Secure, HttpOnly, SameSite)
4. **Masquer la version nginx** (`server_tokens off`)

### Court terme (ce mois)
5. **Implementer le rate limiting** sur `/auth` et `/forgot_password`
6. **Configurer Sentry** avec `allowedDomains` et/ou tunnel backend
7. **Bloquer les source maps** en production
8. **Auditer les permissions RBAC** sur tous les endpoints API

### Moyen terme
9. **Implementer une CSP** stricte
10. **Penetration test** complet de l'API (les endpoints CRUD avec DELETE/PUT sont a risque)
11. **Revue de code** sur la gestion des JWT (stockage, expiration, refresh)
12. **Monitoring** des tentatives de brute force

---

## Methodologie

Cet audit a ete realise de maniere externe (black-box) en analysant :
- Les headers HTTP de `ma-boite-immo.com` et `api.ma-boite-immo.com`
- Le code source HTML de la page de connexion
- Le bundle JavaScript minifie (`index-CezqpEvY.js`)
- Les endpoints API decouverts
- La documentation API Hydra publique (`/docs`)

**Limites** : Cet audit ne couvre pas les vulnerabilites internes (injection SQL, IDOR, privilege escalation) qui necessiteraient un acces authentifie et un test d'intrusion complet.
