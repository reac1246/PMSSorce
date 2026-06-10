<?php
// PMS Setup Script (setup.php)
session_start();

$config_file = __DIR__ . '/config.ini';
$data_dir = __DIR__ . '/data';
$storage_dir = __DIR__ . '/storage';

if (!is_dir($data_dir)) mkdir($data_dir, 0777, true);
if (!is_dir($storage_dir)) mkdir($storage_dir, 0777, true);

$message = "";
$success = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $mode = $_POST['mode'] ?? 'JSON';
    $admin_id = $_POST['admin_id'] ?? '';
    $admin_pw = $_POST['admin_pw'] ?? '';
    $admin_pin = $_POST['admin_pin'] ?? '';

    if (empty($admin_id) || empty($admin_pw) || empty($admin_pin)) {
        $message = "All fields are required.";
    } else {
        // Create Config
        $config_content = "[storage]\nmode = $mode\n\n[admin]\nid = $admin_id\npin = $admin_pin\n";
        file_put_contents($config_file, $config_content);

        // Initialize DB/JSON
        if ($mode === 'SQLITE') {
            $db = new SQLite3($data_dir . '/pms.db');
            $db->exec("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, password TEXT, type TEXT DEFAULT 'regular')");
            // 既存テーブルへのカラム追加チェック
            $res = $db->query("PRAGMA table_info(users)");
            $has_type = false;
            while ($col = $res->fetchArray(SQLITE3_ASSOC)) {
                if ($col['name'] === 'type') { $has_type = true; break; }
            }
            if (!$has_type) { $db->exec("ALTER TABLE users ADD COLUMN type TEXT DEFAULT 'regular'"); }
            
            $db->exec("CREATE TABLE IF NOT EXISTS projects (mgmt_num TEXT PRIMARY KEY, data TEXT)");
            
            $stmt = $db->prepare("INSERT OR REPLACE INTO users (id, password, type) VALUES (:id, :pw, :type)");
            $stmt->bindValue(':id', $admin_id);
            $stmt->bindValue(':pw', $admin_pw);
            $stmt->bindValue(':type', 'regular');
            $stmt->execute();
        } else {
            $users = [$admin_id => ['password' => $admin_pw, 'type' => 'regular']];
            file_put_contents($data_dir . '/users.json', json_encode($users, JSON_PRETTY_PRINT));
            if (!file_exists($data_dir . '/projects.json')) {
                file_put_contents($data_dir . '/projects.json', json_encode([], JSON_PRETTY_PRINT));
            }
        }
        
        $message = "Setup completed successfully!";
        $success = true;
    }
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>PMS Setup Wizard</title>
    <style>
        :root {
            --primary: #6366f1;
            --bg: #0f172a;
            --card: #1e293b;
            --text: #f8fafc;
        }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background: var(--card);
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            width: 400px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        h1 { font-size: 1.5rem; margin-bottom: 1.5rem; text-align: center; color: var(--primary); }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; opacity: 0.8; }
        input, select {
            width: 100%;
            padding: 0.75rem;
            border-radius: 0.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(0,0,0,0.2);
            color: white;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 1rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-weight: bold;
            cursor: pointer;
            margin-top: 1rem;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); filter: brightness(1.1); }
        .alert { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; text-align: center; }
        .alert-success { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; }
        .alert-error { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PMS Setup Wizard</h1>
        
        <?php if ($message): ?>
            <div class="alert <?php echo $success ? 'alert-success' : 'alert-error'; ?>">
                <?php echo $message; ?>
            </div>
        <?php endif; ?>

        <?php if (!$success): ?>
            <form method="POST">
                <div class="form-group">
                    <label>Storage Mode</label>
                    <select name="mode">
                        <option value="JSON">JSON (Recommended for small projects)</option>
                        <option value="SQLITE">SQLite3 (Better performance)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Admin ID</label>
                    <input type="text" name="admin_id" placeholder="admin" required>
                </div>
                <div class="form-group">
                    <label>Admin Password</label>
                    <input type="password" name="admin_pw" required>
                </div>
                <div class="form-group">
                    <label>Security PIN</label>
                    <input type="text" name="admin_pin" placeholder="4-6 digits" required>
                </div>
                <button type="submit">Complete Setup</button>
            </form>
        <?php else: ?>
            <p style="text-align: center; opacity: 0.7;">You can now delete this file or move to index.php.</p>
            <button onclick="location.href='index.php'">Go to Dashboard</button>
        <?php endif; ?>
    </div>
</body>
</html>
