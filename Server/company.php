<?php
// PMS Corporate Portal (company.php)
session_start();
require_once __DIR__ . '/api.php';

$is_logged_in = isset($_SESSION['corp_user']);
$user_id = $_SESSION['corp_user'] ?? '';
$error = "";
$message = "";

// Handle Login
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
    $id = $_POST['id'] ?? '';
    $pw = $_POST['pw'] ?? '';
    $users = get_users();

    if (isset($users[$id]) && $users[$id]['password'] === $pw && $users[$id]['type'] === 'corporate') {
        $_SESSION['corp_user'] = $id;
        header("Location: company.php");
        exit;
    } else {
        $error = "Invalid Corporate ID or Password.";
    }
}

// Handle Logout
if (isset($_GET['logout'])) {
    session_destroy();
    header("Location: company.php");
    exit;
}

// Handle Upload (Document)
if ($is_logged_in && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['upload'])) {
    $doc_name = $_POST['doc_name'] ?? '';
    $mgmt_num = $_POST['mgmt_num'] ?? ''; // Optional, auto-generated if empty
    
    if (isset($_FILES['file']) && $_FILES['file']['error'] === 0) {
        // We can reuse api.php setup logic by calling it via include or just reimplementing
        // For simplicity, let's call the logic directly
        if (empty($mgmt_num)) {
            $mgmt_num = "DOC_" . $user_id . "_" . bin2hex(random_bytes(4));
        }
        $mgmt_hash = get_mgmt_hash($mgmt_num);
        $project_storage = __DIR__ . '/storage/' . $mgmt_hash;
        if (!is_dir($project_storage)) mkdir($project_storage, 0777, true);

        $filename = "v1.0.0.zip";
        if (move_uploaded_file($_FILES['file']['tmp_name'], $project_storage . '/' . $filename)) {
            $projects = get_projects();
            $projects[$mgmt_hash] = [
                'project_name' => $doc_name, // This is our DocumentsName
                'management_number' => $mgmt_num,
                'latest_version' => '1.0.0',
                'versions' => ['1.0.0'],
                'created_at' => date('c'),
                'updated_at' => date('c'),
                'owner' => $user_id
            ];
            save_projects($projects);
            $message = "Document '$doc_name' uploaded successfully. ID: $mgmt_num";
        } else {
            $error = "Upload failed.";
        }
    } else {
        $error = "Please select a valid ZIP file.";
    }
}

$my_docs = [];
if ($is_logged_in) {
    $all = get_projects();
    foreach ($all as $h => $p) {
        if (($p['owner'] ?? '') === $user_id) {
            $my_docs[$h] = $p;
        }
    }
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Corporate Document Portal</title>
    <style>
        :root { --primary: #6366f1; --bg: #0f172a; --card: #1e293b; --text: #f8fafc; }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
        .navbar { background: var(--card); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .logo { font-size: 1.2rem; font-weight: bold; color: var(--primary); }
        .container { max-width: 1000px; margin: 3rem auto; padding: 0 2rem; }
        .card { background: var(--card); padding: 2rem; border-radius: 1rem; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 2rem; }
        .login-box { max-width: 400px; margin: 10rem auto; }
        .form-group { margin-bottom: 1.5rem; }
        label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; opacity: 0.8; }
        input { width: 100%; padding: 0.8rem; border-radius: 0.5rem; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); color: white; box-sizing: border-box; }
        button { width: 100%; padding: 1rem; background: var(--primary); color: white; border: none; border-radius: 0.5rem; cursor: pointer; font-weight: bold; }
        .alert { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1.5rem; text-align: center; }
        .alert-success { background: rgba(34, 197, 94, 0.1); color: #4ade80; }
        .alert-error { background: rgba(239, 68, 68, 0.1); color: #f87171; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { text-align: left; padding: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
        th { opacity: 0.6; font-size: 0.8rem; text-transform: uppercase; }
        .dl-btn { color: var(--primary); text-decoration: none; font-weight: bold; font-size: 0.9rem; }
    </style>
</head>
<body>

<?php if (!$is_logged_in): ?>
    <div class="login-box card">
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">🏢</div>
            <h1 style="margin: 1rem 0;">Corporate Portal</h1>
            <p style="opacity: 0.6; font-size: 0.9rem;">Sign in to manage your documents</p>
        </div>
        <?php if ($error): ?><div class="alert alert-error"><?php echo $error; ?></div><?php endif; ?>
        <form method="POST">
            <div class="form-group">
                <label>Corporate ID</label>
                <input type="text" name="id" required placeholder="Enter ID">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="pw" required placeholder="••••••••">
            </div>
            <button type="submit" name="login">Sign In</button>
        </form>
    </div>
<?php else: ?>
    <div class="navbar">
        <div class="logo">Corporate Portal <span style="font-weight: normal; opacity: 0.5;">| <?php echo htmlspecialchars($user_id); ?></span></div>
        <a href="?logout=1" style="color: inherit; opacity: 0.6; text-decoration: none; font-size: 0.9rem;">Logout</a>
    </div>

    <div class="container">
        <?php if ($message): ?><div class="alert alert-success"><?php echo $message; ?></div><?php endif; ?>
        <?php if ($error): ?><div class="alert alert-error"><?php echo $error; ?></div><?php endif; ?>

        <div class="card">
            <h2>Upload New Document</h2>
            <form method="POST" enctype="multipart/form-data">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div class="form-group">
                        <label>DocumentsName (Label)</label>
                        <input type="text" name="doc_name" required placeholder="e.g. Q2 Report 2026">
                    </div>
                    <div class="form-group">
                        <label>Management ID (Optional)</label>
                        <input type="text" name="mgmt_num" placeholder="Leave blank for auto-gen">
                    </div>
                </div>
                <div class="form-group">
                    <label>File (ZIP Archive)</label>
                    <input type="file" name="file" accept=".zip" required>
                </div>
                <button type="submit" name="upload" style="width: auto; padding: 0.8rem 3rem;">Upload Document</button>
            </form>
        </div>

        <div class="card">
            <h2>Your Documents</h2>
            <table>
                <thead>
                    <tr>
                        <th>Document Name</th>
                        <th>Management ID</th>
                        <th>Uploaded At</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($my_docs as $h => $d): ?>
                        <tr>
                            <td><strong><?php echo htmlspecialchars($d['project_name']); ?></strong></td>
                            <td><code><?php echo htmlspecialchars($d['management_number']); ?></code></td>
                            <td><?php echo date('Y/m/d H:i', strtotime($d['created_at'])); ?></td>
                            <td>
                                <a href="api.php?action=download&management_number=<?php echo urlencode($d['management_number']); ?>&login_id=<?php echo urlencode($user_id); ?>&login_pw=<?php echo urlencode($users[$user_id]['password']); ?>" class="dl-btn">Download</a>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                    <?php if (empty($my_docs)): ?>
                        <tr><td colspan="4" style="text-align: center; opacity: 0.4; padding: 3rem;">No documents uploaded yet.</td></tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
<?php endif; ?>

</body>
</html>
