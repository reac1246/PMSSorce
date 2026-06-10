<?php
// PMS Secure Download Page (secure_download.php)
session_start();
require_once __DIR__ . '/api.php';

$mgmt_num = $_GET['mgmt_num'] ?? ($_POST['mgmt_num'] ?? '');
if (empty($mgmt_num)) {
    header('Location: index.php');
    exit;
}

$error = "";
$project_info = null;

// Get project info (publicly if not secure, or just check existence)
$projects = get_projects();
$hash = get_mgmt_hash($mgmt_num);
if (!isset($projects[$hash])) {
    die("Project not found.");
}
$project_info = $projects[$hash];

// Handle Login & Download
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $id = $_POST['id'] ?? '';
    $pw = $_POST['pw'] ?? '';

    if (check_auth($id, $pw)) {
        // Redirect to API download with credentials
        $url = "api.php?action=download&management_number=" . urlencode($mgmt_num) . "&login_id=" . urlencode($id) . "&login_pw=" . urlencode($pw);
        header("Location: $url");
        exit;
    } else {
        $error = "Invalid ID or Password.";
    }
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Secure Download - <?php echo htmlspecialchars($project_info['project_name']); ?></title>
    <style>
        :root {
            --primary: #6366f1;
            --danger: #ef4444;
            --bg: #0f172a;
            --card: #1e293b;
            --text: #f8fafc;
        }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .login-box { width: 100%; max-width: 400px; background: var(--card); padding: 2.5rem; border-radius: 1.5rem; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }
        .project-meta { text-align: center; margin-bottom: 2rem; }
        .project-meta h1 { margin: 0; font-size: 1.5rem; color: var(--primary); }
        .project-meta p { opacity: 0.6; font-size: 0.9rem; margin-top: 0.5rem; }
        .secure-badge { display: inline-block; padding: 0.25rem 0.75rem; background: rgba(239, 68, 68, 0.1); color: var(--danger); border-radius: 2rem; font-size: 0.75rem; font-weight: 700; margin-bottom: 1rem; }
        .form-group { margin-bottom: 1.5rem; }
        label { display: block; margin-bottom: 0.5rem; font-size: 0.85rem; opacity: 0.8; }
        input { width: 100%; padding: 0.8rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); color: white; box-sizing: border-box; outline: none; transition: border-color 0.2s; }
        input:focus { border-color: var(--primary); }
        button { width: 100%; padding: 1rem; background: var(--primary); color: white; border: none; border-radius: 0.75rem; cursor: pointer; font-weight: 700; font-size: 1rem; transition: transform 0.2s, filter 0.2s; }
        button:hover { transform: translateY(-2px); filter: brightness(1.1); }
        .error { color: var(--danger); text-align: center; font-size: 0.9rem; margin-bottom: 1rem; }
        .back-link { text-align: center; margin-top: 1.5rem; font-size: 0.85rem; }
        .back-link a { color: inherit; opacity: 0.5; text-decoration: none; }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="project-meta">
            <div class="secure-badge">SECURE PROJECT</div>
            <h1><?php echo htmlspecialchars($project_info['project_name']); ?></h1>
            <p><?php echo htmlspecialchars($mgmt_num); ?></p>
        </div>

        <?php if ($error): ?><div class="error"><?php echo $error; ?></div><?php endif; ?>

        <form method="POST">
            <input type="hidden" name="mgmt_num" value="<?php echo htmlspecialchars($mgmt_num); ?>">
            <div class="form-group">
                <label>User ID</label>
                <input type="text" name="id" required placeholder="Enter your ID">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="pw" required placeholder="Enter password">
            </div>
            <button type="submit">Unlock & Download</button>
        </form>

        <div class="back-link">
            <a href="index.php">← Back to Search</a>
        </div>
    </div>
</body>
</html>
