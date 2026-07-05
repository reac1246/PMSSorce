<?php
// PMS Administrator Panel (admin.php)
session_start();

$config_file = __DIR__ . '/config.ini';
if (!file_exists($config_file)) {
    header('Location: setup.php');
    exit;
}

require_once __DIR__ . '/api.php';
$config = parse_ini_file($config_file, true);
$admin_id_config = $config['admin']['id'] ?? '';
$admin_pin_config = $config['admin']['pin'] ?? '';

$error = "";
$is_logged_in = $_SESSION['admin_logged_in'] ?? false;

// Handle Logout
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: admin.php');
    exit;
}

// Handle Login
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
    $id = $_POST['id'] ?? '';
    $pw = $_POST['pw'] ?? '';
    $pin = $_POST['pin'] ?? '';

    if ($id === $admin_id_config && $pin === $admin_pin_config && check_auth($id, $pw)) {
        $_SESSION['admin_logged_in'] = true;
        $is_logged_in = true;
    } else {
        $error = "Invalid credentials or Security PIN.";
    }
}

// Handle User Creation
if ($is_logged_in && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['create_user'])) {
    $new_id = $_POST['new_id'] ?? '';
    $new_pw = $_POST['new_pw'] ?? '';
    $type = $_POST['type'] ?? 'regular';
    if ($new_id && $new_pw) {
        $users = get_users();
        $users[$new_id] = ['password' => $new_pw, 'type' => $type];
        save_users($users);
        $message = "User '$new_id' ($type) created successfully.";
    }
}

// Handle User Deletion
if ($is_logged_in && isset($_GET['delete_user'])) {
    $del_id = $_GET['delete_user'];
    if ($del_id !== $admin_id_config) {
        $users = get_users();
        unset($users[$del_id]);
        save_users($users);
        header('Location: admin.php');
        exit;
    }
}

// Handle ChangeKey Generation
if ($is_logged_in && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['gen_key'])) {
    $new_key = bin2hex(random_bytes(8));
    $config_data = parse_ini_file($config_file, true);
    $config_data['admin']['change_key'] = $new_key;
    
    // INIファイルを再構築
    $content = "";
    foreach ($config_data as $section => $values) {
        $content .= "[$section]\n";
        foreach ($values as $k => $v) {
            $content .= "$k = $v\n";
        }
    }
    file_put_contents($config_file, $content);
    $message = "ChangeKey generated: $new_key";
    $config = $config_data; // 反映
}

// Handle Update Distribution
if ($is_logged_in && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['distribute_update'])) {
    $version = $_POST['version'] ?? '';
    $release_notes = $_POST['release_notes'] ?? '';
    
    if (isset($_FILES['setup_exe']) && $_FILES['setup_exe']['error'] === UPLOAD_ERR_OK) {
        $updates_dir = __DIR__ . '/updates';
        if (!is_dir($updates_dir)) mkdir($updates_dir, 0777, true);
        
        $target_file = $updates_dir . '/PMS_Setup.exe';
        move_uploaded_file($_FILES['setup_exe']['tmp_name'], $target_file);
        
        $json_data = [
            'version' => $version,
            'download_url' => 'updates/PMS_Setup.exe',
            'release_notes' => $release_notes
        ];
        file_put_contents($updates_dir . '/latest.json', json_encode($json_data, JSON_PRETTY_PRINT));
        $message = "Update v{$version} distributed successfully.";
    } else {
        $error = "Failed to upload setup executable.";
    }
}

$all_projects = $is_logged_in ? get_projects() : [];
$all_users = $is_logged_in ? get_users() : [];

?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>PMS Admin Panel</title>
    <style>
        :root {
            --primary: #6366f1;
            --danger: #ef4444;
            --bg: #0f172a;
            --card: #1e293b;
            --text: #f8fafc;
        }
        body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
        .container { max-width: 1000px; margin: 4rem auto; padding: 0 2rem; }
        .login-box { max-width: 400px; margin: 10rem auto; background: var(--card); padding: 2rem; border-radius: 1rem; border: 1px solid rgba(255,255,255,0.1); }
        h1, h2 { color: var(--primary); }
        .form-group { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.5rem; opacity: 0.8; font-size: 0.9rem; }
        input { width: 100%; padding: 0.75rem; border-radius: 0.5rem; border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); color: white; box-sizing: border-box; }
        button { padding: 0.75rem; background: var(--primary); color: white; border: none; border-radius: 0.5rem; cursor: pointer; font-weight: bold; width: 100%; }
        .btn-danger { background: var(--danger); }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: var(--card); border-radius: 0.5rem; overflow: hidden; }
        th, td { padding: 1rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.05); }
        th { background: rgba(255,255,255,0.05); font-weight: 600; }
        .nav { display: flex; justify-content: space-between; align-items: center; padding: 1rem 2rem; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .card { background: var(--card); padding: 1.5rem; border-radius: 1rem; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 2rem; }
        
        .grid-form { display: grid; grid-template-columns: 1fr 1fr auto auto; gap: 0.5rem; margin-bottom: 1.5rem; }
        @media (max-width: 768px) {
            .grid-form { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <?php if (!$is_logged_in): ?>
        <div class="login-box">
            <h1>Admin Login</h1>
            <?php if ($error): ?><p style="color: var(--danger);"><?php echo $error; ?></p><?php endif; ?>
            <form method="POST">
                <input type="hidden" name="login" value="1">
                <div class="form-group">
                    <label>Admin ID</label>
                    <input type="text" name="id" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="pw" required>
                </div>
                <div class="form-group">
                    <label>Security PIN</label>
                    <input type="text" name="pin" required>
                </div>
                <button type="submit">Login</button>
            </form>
            <p style="text-align: center; margin-top: 1rem; font-size: 0.8rem; opacity: 0.5;"><a href="index.php" style="color: inherit;">Back to Search</a></p>
        </div>
    <?php else: ?>
        <nav class="nav">
            <div style="font-weight: 800; font-size: 1.2rem;">PMS Admin Panel</div>
            <div>
                <a href="index.php" style="color: var(--text); text-decoration: none; margin-right: 1.5rem;">Dashboard</a>
                <a href="?logout=1" style="color: var(--danger); text-decoration: none;">Logout</a>
            </div>
        </nav>

        <div class="container">
            <?php if (isset($message)): ?><p style="color: #10b981; font-weight: bold; padding: 1rem; background: rgba(16,185,129,0.1); border-radius: 0.5rem;"><?php echo $message; ?></p><?php endif; ?>
            <?php if (isset($error) && $error): ?><p style="color: var(--danger); font-weight: bold; padding: 1rem; background: rgba(239,68,68,0.1); border-radius: 0.5rem;"><?php echo $error; ?></p><?php endif; ?>
            
            <div class="card">
                <h2>Update Distribution</h2>
                <form method="POST" enctype="multipart/form-data" style="display: grid; gap: 1rem; grid-template-columns: 1fr 2fr; align-items: end;">
                    <div style="grid-column: 1 / -1;">
                        <label>Setup Executable (PMS_Setup.exe)</label>
                        <input type="file" name="setup_exe" accept=".exe" required style="background: transparent; border: 1px dashed rgba(255,255,255,0.3); padding: 1rem;">
                    </div>
                    <div>
                        <label>Version Number (e.g. 1.0.6)</label>
                        <input type="text" name="version" required>
                    </div>
                    <div>
                        <label>Release Notes</label>
                        <input type="text" name="release_notes">
                    </div>
                    <div style="grid-column: 1 / -1;">
                        <button type="submit" name="distribute_update" style="width: auto; padding: 0.75rem 2rem;">Distribute Update</button>
                    </div>
                </form>
            </div>

            <div class="card">
                <h2>System Settings</h2>
                <form method="POST">
                    <input type="hidden" name="gen_key" value="1">
                    <p style="font-size: 0.9rem; opacity: 0.7; margin-bottom: 1rem;">
                        管理番号のUserID部分を変更するには 1回限りの <strong>ChangeKey</strong> が必要です。<br>
                        現在の鍵: <code><?php echo htmlspecialchars($config['admin']['change_key'] ?? 'None'); ?></code>
                    </p>
                    <button type="submit" style="width: auto; padding: 0.75rem 2rem;">Generate New ChangeKey</button>
                </form>
            </div>

            <div class="card">
                <h2>User Management</h2>
                <form method="POST" class="grid-form">
                    <input type="text" name="new_id" placeholder="User/Company ID" required>
                    <input type="password" name="new_pw" placeholder="Password" required>
                    <select name="type" style="padding: 0.75rem; border-radius: 0.5rem; background: rgba(0,0,0,0.2); color: white; border: 1px solid rgba(255,255,255,0.1);">
                        <option value="regular">Regular User</option>
                        <option value="corporate">Corporate</option>
                    </select>
                    <button type="submit" name="create_user" style="width: 100%;">Create</button>
                </form>

                <table>
                    <thead>
                        <tr>
                            <th>User ID</th>
                            <th>Type</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($all_users as $uid => $udata): ?>
                            <tr>
                                <td><?php echo htmlspecialchars($uid); ?></td>
                                <td><span style="padding: 0.2rem 0.5rem; border-radius: 0.3rem; font-size: 0.8rem; background: <?php echo ($udata['type'] ?? 'regular') === 'corporate' ? '#6366f1' : 'rgba(255,255,255,0.1)'; ?>"><?php echo htmlspecialchars($udata['type'] ?? 'regular'); ?></span></td>
                                <td>
                                    <?php if ($uid !== $admin_id_config): ?>
                                        <a href="?delete_user=<?php echo urlencode($uid); ?>" style="color: #ef4444;" onclick="return confirm('Delete this user?')">Delete</a>
                                    <?php endif; ?>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h2>Project List</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Project Name</th>
                            <th>Management Number</th>
                            <th>Version</th>
                            <th>Owner</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($all_projects as $hash => $data): 
                            $raw_num = $data['management_number'] ?? 'Unknown';
                        ?>
                            <tr>
                                <td><strong><?php echo htmlspecialchars($data['project_name']); ?></strong></td>
                                <td><code><?php echo htmlspecialchars($raw_num); ?></code></td>
                                <td>v<?php echo htmlspecialchars($data['latest_version']); ?></td>
                                <td><?php echo htmlspecialchars($data['owner']); ?></td>
                                <td style="display: flex; gap: 0.5rem;">
                                    <a href="api.php?action=download&management_number=<?php echo urlencode($raw_num); ?>&login_id=<?php echo urlencode($admin_id_config); ?>&login_pw=admin_bypass" 
                                       style="padding: 0.3rem 0.6rem; background: rgba(16, 185, 129, 0.1); color: #10b981; border-radius: 0.4rem; text-decoration: none; font-size: 0.8rem; font-weight: bold;">
                                       DL
                                    </a>
                                    <a href="#" onclick="renameProject('<?php echo htmlspecialchars($raw_num); ?>')"
                                       style="padding: 0.3rem 0.6rem; background: rgba(99, 102, 241, 0.1); color: var(--primary); border-radius: 0.4rem; text-decoration: none; font-size: 0.8rem; font-weight: bold;">
                                       Rename
                                    </a>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>

            <script>
            function renameProject(oldId) {
                const newId = prompt('新しい管理番号を入力してください:', oldId);
                if (newId && newId !== oldId) {
                    const changeKey = '<?php echo $config['admin']['change_key'] ?? ''; ?>';
                    fetch('api.php?action=edit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            login_id: '<?php echo $admin_id_config; ?>',
                            login_pw: 'admin_bypass',
                            old_management_number: oldId,
                            new_management_number: newId,
                            change_key: changeKey
                        })
                    }).then(r => r.json()).then(data => {
                        if (data.status === 'ok') {
                            alert('リネームが完了しました。');
                            location.reload();
                        } else {
                            alert('エラー: ' + data.message);
                        }
                    });
                }
            }
            </script>
        </div>
    <?php endif; ?>
</body>
</html>
