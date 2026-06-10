<?php
// PMS Dashboard (index.php)
session_start();

$config_file = __DIR__ . '/config.ini';
if (!file_exists($config_file)) {
    header('Location: setup.php');
    exit;
}

require_once __DIR__ . '/api.php'; // Reuse get_projects() etc.

$search_result = null;
$error = "";

if (isset($_GET['mgmt_num'])) {
    $num = $_GET['mgmt_num'];
    $hash = get_mgmt_hash($num);
    $projects = get_projects();
    if (isset($projects[$hash])) {
        $search_result = $projects[$hash];
    } else {
        $error = "Project not found with this Management Number.";
    }
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PMS Data Center Dashboard</title>
    <style>
        :root {
            --primary: #6366f1;
            --secondary: #ec4899;
            --bg: #0f172a;
            --card: #1e293b;
            --text: #f8fafc;
            --muted: #94a3b8;
        }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Inter', system-ui, sans-serif;
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }
        .navbar {
            padding: 1.5rem 2rem;
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .logo { font-size: 1.5rem; font-weight: 800; background: linear-gradient(to right, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        
        .main-content {
            max-width: 1000px;
            margin: 4rem auto;
            padding: 0 2rem;
        }
        .hero { text-align: center; margin-bottom: 4rem; }
        .hero h1 { font-size: 3rem; margin-bottom: 1rem; letter-spacing: -0.02em; }
        .hero p { color: var(--muted); font-size: 1.2rem; }

        .search-box {
            background: var(--card);
            padding: 0.5rem;
            border-radius: 1rem;
            display: flex;
            gap: 0.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
            max-width: 600px;
            margin: 0 auto;
        }
        .search-box input {
            flex: 1;
            background: transparent;
            border: none;
            padding: 1rem;
            color: white;
            font-size: 1rem;
            outline: none;
        }
        .search-box button {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .search-box button:hover { transform: scale(1.02); filter: brightness(1.1); }

        .result-card {
            background: var(--card);
            border-radius: 1.5rem;
            padding: 2.5rem;
            margin-top: 3rem;
            border: 1px solid rgba(255,255,255,0.1);
            animation: slideUp 0.4s ease-out;
        }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.8rem;
            font-weight: 600;
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
            margin-bottom: 1rem;
        }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem; margin-top: 2rem; }
        .info-item label { display: block; color: var(--muted); font-size: 0.9rem; margin-bottom: 0.5rem; }
        .info-item span { font-size: 1.1rem; font-weight: 500; }

        .footer { text-align: center; margin-top: 8rem; padding-bottom: 4rem; color: var(--muted); font-size: 0.9rem; }
        .admin-link { color: var(--primary); text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="logo">PMS Data Center</div>
        <a href="admin.php" class="admin-link">Administrator Portal</a>
    </nav>

    <div class="main-content">
        <div class="hero">
            <h1>Search Project</h1>
            <p>Access your project data instantly using the PMS Management Number.</p>
        </div>

        <form method="GET" class="search-box">
            <input type="text" name="mgmt_num" placeholder="Enter PMS Management Number (e.g. PMS_user_xxxx)" value="<?php echo htmlspecialchars($_GET['mgmt_num'] ?? ''); ?>" required>
            <button type="submit">Lookup</button>
        </form>

        <?php if ($error): ?>
            <p style="text-align: center; color: #f87171; margin-top: 2rem;"><?php echo $error; ?></p>
        <?php endif; ?>

        <?php if ($search_result): ?>
            <div class="result-card">
                <div class="status-badge">Active Project</div>
                <h2 style="font-size: 2rem; margin: 0 0 0.5rem 0;"><?php echo htmlspecialchars($search_result['project_name']); ?></h2>
                <p style="color: var(--muted); margin: 0;"><?php echo htmlspecialchars($search_result['management_number']); ?></p>

                <div class="grid">
                    <div class="info-item">
                        <label>Latest Version</label>
                        <span>v<?php echo htmlspecialchars($search_result['latest_version']); ?></span>
                    </div>
                    <div class="info-item">
                        <label>Owner</label>
                        <span><?php echo htmlspecialchars($search_result['owner']); ?></span>
                    </div>
                    <div class="info-item">
                        <label>Created At</label>
                        <span><?php echo date('Y/m/d H:i', strtotime($search_result['created_at'])); ?></span>
                    </div>
                    <div class="info-item">
                        <label>Last Synchronized</label>
                        <span><?php echo date('Y/m/d H:i', strtotime($search_result['updated_at'])); ?></span>
                    </div>
                </div>

                <div style="margin-top: 3rem; display: flex; gap: 1rem;">
                    <?php if (is_secure_mgmt($search_result['management_number'])): ?>
                        <a href="secure_download.php?mgmt_num=<?php echo urlencode($search_result['management_number']); ?>" class="admin-link" style="padding: 1rem 2rem; background: rgba(99, 102, 241, 0.1); color: #6366f1; border-radius: 0.75rem; border: 1px solid rgba(99, 102, 241, 0.2); text-decoration: none; font-weight: bold;">
                            Unlock & Download (Secure)
                        </a>
                    <?php else: ?>
                        <a href="api.php?action=download&management_number=<?php echo urlencode($search_result['management_number']); ?>&login_id=public&login_pw=public" class="admin-link" style="padding: 1rem 2rem; background: rgba(255,255,255,0.05); border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.1); text-decoration: none;">
                            Download Latest Build
                        </a>
                    <?php endif; ?>
                </div>
                <p style="font-size: 0.8rem; color: var(--muted); margin-top: 1rem;">* Download requires appropriate credentials if not public.</p>
            </div>
        <?php endif; ?>
    </div>

    <footer class="footer">
        &copy; 2026 PMS Data Center Solutions. All rights reserved.
    </footer>
</body>
</html>
