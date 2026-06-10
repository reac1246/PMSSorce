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
    if ($new_id && $new_pw) {
        $users = get_users();
        $users[$new_id] = $new_pw;
        save_users($users);
        $message = "User '$new_id' created successfully.";
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
        button { width: 100%; padding: 0.75rem; background: var(--primary); color: white; border: none; border-radius: 0.5rem; cursor: pointer; font-weight: bold; }
        .btn-danger { background: var(--danger); }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: var(--card); border-radius: 0.5rem; overflow: hidden; }
        th, td { padding: 1rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.05); }
        th { background: rgba(255,255,255,0.05); font-weight: 600; }
        .nav { display: flex; justify-content: space-between; align-items: center; padding: 1rem 2rem; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .card { background: var(--card); padding: 1.5rem; border-radius: 1rem; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 2rem; }
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
            <div class="card">
                <h2>User Management</h2>
                <form method="POST" style="display: flex; gap: 1rem; align-items: flex-end;">
                    <input type="hidden" name="create_user" value="1">
                    <div class="form-group" style="flex: 1;">
                        <label>New User ID</label>
                        <input type="text" name="new_id" required>
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <label>Password</label>
                        <input type="password" name="new_pw" required>
                    </div>
                    <button type="submit" style="width: auto; padding: 0.75rem 2rem;">Create User</button>
                </form>

                <table>
                    <thead>
                        <tr>
                            <th>User ID</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($all_users as $id => $pw): ?>
                            <tr>
                                <td><?php echo htmlspecialchars($id); ?></td>
                                <td>
                                    <?php if ($id !== $admin_id_config): ?>
                                        <a href="?delete_user=<?php echo urlencode($id); ?>" style="color: var(--danger);" onclick="return confirm('Delete this user?')">Delete</a>
                                    <?php else: ?>
                                        <span style="opacity: 0.5;">Admin (System)</span>
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
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($all_projects as $num => $data): ?>
                            <tr>
                                <td><?php echo htmlspecialchars($data['project_name']); ?></td>
                                <td><code><?php echo htmlspecialchars($num); ?></code></td>
                                <td><?php echo htmlspecialchars($data['latest_version']); ?></td>
                                <td><?php echo htmlspecialchars($data['owner']); ?></td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    <?php endif; ?>
</body>
</html>
