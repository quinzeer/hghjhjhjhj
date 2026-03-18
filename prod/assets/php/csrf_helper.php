<?php
/**
 * [FIX #3] Helper CSRF pour Twimmo.net
 *
 * Génère et valide des tokens CSRF pour protéger les formulaires.
 *
 * Utilisation :
 *   1. Dans le contrôleur qui affiche le formulaire :
 *      require_once 'assets/php/csrf_helper.php';
 *      $csrfToken = CsrfHelper::generateToken();
 *
 *   2. Dans le template HTML du formulaire :
 *      <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($csrfToken) ?>">
 *
 *   3. Dans le contrôleur qui traite le POST :
 *      require_once 'assets/php/csrf_helper.php';
 *      if (!CsrfHelper::validateToken($_POST['csrf_token'] ?? '')) {
 *          http_response_code(403);
 *          die('Token CSRF invalide. Veuillez rafraîchir la page.');
 *      }
 */

class CsrfHelper
{
    private const TOKEN_NAME = 'csrf_token';
    private const TOKEN_LENGTH = 32;

    /**
     * Génère un token CSRF unique et le stocke en session.
     */
    public static function generateToken(): string
    {
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

        $token = bin2hex(random_bytes(self::TOKEN_LENGTH));
        $_SESSION[self::TOKEN_NAME] = $token;

        return $token;
    }

    /**
     * Valide un token CSRF soumis par le formulaire.
     * Le token est consommé après validation (usage unique).
     */
    public static function validateToken(string $submittedToken): bool
    {
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

        if (empty($submittedToken) || empty($_SESSION[self::TOKEN_NAME])) {
            return false;
        }

        $storedToken = $_SESSION[self::TOKEN_NAME];

        // Comparaison en temps constant pour éviter les timing attacks
        $isValid = hash_equals($storedToken, $submittedToken);

        // Supprimer le token après usage (protection contre le replay)
        unset($_SESSION[self::TOKEN_NAME]);

        return $isValid;
    }

    /**
     * Génère le champ HTML hidden pour le formulaire.
     */
    public static function getHiddenField(): string
    {
        $token = self::generateToken();
        return '<input type="hidden" name="' . self::TOKEN_NAME . '" value="' . htmlspecialchars($token, ENT_QUOTES, 'UTF-8') . '">';
    }
}
