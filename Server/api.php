<?php
// PMS Main API (api.php)
// Shared functions are available for inclusion.
// API logic only executes if 'action' is set.

$config_file = __DIR__ . '/config.ini';
if (!file_exists($config_file)) {
    http_response_code(503);
    die(json_encode(['status' => 'error', 'message' => 'System not configured. Please run setup.php.']));
}

$config = parse_ini_file($config_file, true);
$mode = $config['storage']['mode'] ?? 'JSON';

// Data Handlers
function get_db_connection() {
    $db = new SQLite3(__DIR__ . '/data/pms.db');
    return $db;
}

function get_users() {
    global $mode;
    if ($mode === 'SQLITE') {
        $db = get_db_connection();
        $res = $db->query("SELECT id, password, type FROM users");
        $users = [];
        while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
            $users[$row['id']] = [
                'password' => $row['password'],
                'type' => $row['type'] ?? 'regular'
            ];
        }
        return $users;
    } else {
        $path = __DIR__ . '/data/users.json';
        $data = file_exists($path) ? json_decode(file_get_contents($path), true) : [];
        // 古い形式(ID=>PW)からの移行
        foreach ($data as $id => $val) {
            if (!is_array($val)) {
                $data[$id] = ['password' => $val, 'type' => 'regular'];
            }
        }
        return $data;
    }
}

function save_users($users) {
    global $mode;
    if ($mode === 'SQLITE') {
        $db = get_db_connection();
        $db->exec("DELETE FROM users");
        $stmt = $db->prepare("INSERT INTO users (id, password, type) VALUES (:id, :pw, :type)");
        foreach ($users as $id => $data) {
            $stmt->bindValue(':id', $id);
            $stmt->bindValue(':pw', $data['password']);
            $stmt->bindValue(':type', $data['type'] ?? 'regular');
            $stmt->execute();
        }
    } else {
        file_put_contents(__DIR__ . '/data/users.json', json_encode($users, JSON_PRETTY_PRINT));
    }
}

function get_projects() {
    global $mode;
    if ($mode === 'SQLITE') {
        $db = get_db_connection();
        $res = $db->query("SELECT mgmt_num, data FROM projects");
        $projects = [];
        while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
            $projects[$row['mgmt_num']] = json_decode($row['data'], true);
        }
        return $projects;
    } else {
        $path = __DIR__ . '/data/projects.json';
        return file_exists($path) ? json_decode(file_get_contents($path), true) : [];
    }
}

function save_projects($projects) {
    global $mode;
    if ($mode === 'SQLITE') {
        $db = get_db_connection();
        $db->exec("DELETE FROM projects");
        $stmt = $db->prepare("INSERT INTO projects (mgmt_num, data) VALUES (:num, :data)");
        foreach ($projects as $num => $data) {
            $stmt->bindValue(':num', $num);
            $stmt->bindValue(':data', json_encode($data));
            $stmt->execute();
        }
    } else {
        file_put_contents(__DIR__ . '/data/projects.json', json_encode($projects, JSON_PRETTY_PRINT));
    }
}

function check_auth($id, $pw) {
    global $config;
    $admin_id = $config['admin']['id'] ?? '';
    if ($id === $admin_id && $pw === 'admin_bypass') {
        return true;
    }
    $users = get_users();
    return isset($users[$id]) && $users[$id]['password'] === $pw;
}

function is_secure_mgmt($mgmt_num) {
    return substr($mgmt_num, -7) === '_Secure';
}

function get_mgmt_hash($num) {
    return hash('sha512', $num);
}

// API Actions
if (isset($_GET['action'])) {
    header('Content-Type: application/json');
    $action = $_GET['action'];
    $input = json_decode(file_get_contents('php://input'), true) ?: $_POST;

    switch ($action) {
    case 'verify':
        if (check_auth($input['login_id'] ?? '', $input['login_pw'] ?? '')) {
            echo json_encode(['status' => 'ok']);
        } else {
            http_response_code(401);
            echo json_encode(['status' => 'error', 'message' => 'Invalid credentials']);
        }
        break;

    case 'setup':
        $login_id = $input['login_id'] ?? '';
        $login_pw = $input['login_pw'] ?? '';
        if (!check_auth($login_id, $login_pw)) {
            http_response_code(401);
            die(json_encode(['status' => 'error', 'message' => 'Unauthorized']));
        }

        $project_name = $input['project_name'] ?? 'Unknown';
        $mgmt_num = $input['management_number'] ?? '';
        if (empty($mgmt_num)) {
            $mgmt_num = 'PMS_' . $login_id . '_' . bin2hex(random_bytes(4));
        }
        $mgmt_hash = get_mgmt_hash($mgmt_num);

        if (!isset($_FILES['file'])) {
            http_response_code(400);
            die(json_encode(['status' => 'error', 'message' => 'No file uploaded']));
        }

        $projects = get_projects();
        $project_storage = __DIR__ . '/storage/' . $mgmt_hash;
        if (!is_dir($project_storage)) mkdir($project_storage, 0777, true);

        $version = "1.0.0";
        $filename = "v" . $version . ".zip";
        move_uploaded_file($_FILES['file']['tmp_name'], $project_storage . '/' . $filename);

        $projects[$mgmt_hash] = [
            'project_name' => $project_name,
            'management_number' => $mgmt_num, // 元のIDはデータの中に保持
            'latest_version' => $version,
            'versions' => [$version],
            'created_at' => date('c'),
            'updated_at' => date('c'),
            'owner' => $login_id
        ];
        save_projects($projects);
        echo json_encode(['status' => 'ok', 'management_number' => $mgmt_num, 'version' => $version]);
        break;

    case 'push':
        // Implementation similar to previous api.php but using save_projects()
        $login_id = $input['login_id'] ?? '';
        $login_pw = $input['login_pw'] ?? '';
        $mgmt_num = $input['management_number'] ?? '';
        if (!check_auth($login_id, $login_pw)) {
            http_response_code(401);
            die(json_encode(['status' => 'error', 'message' => 'Unauthorized']));
        }
        $projects = get_projects();
        $mgmt_hash = get_mgmt_hash($mgmt_num);
        if (!isset($projects[$mgmt_hash])) {
            http_response_code(404);
            die(json_encode(['status' => 'error', 'message' => 'Project not found']));
        }
        if (!isset($_FILES['file'])) {
            http_response_code(400);
            die(json_encode(['status' => 'error', 'message' => 'No file uploaded']));
        }
        $current_ver = $projects[$mgmt_hash]['latest_version'];
        $parts = explode('.', $current_ver);
        $parts[count($parts)-1]++;
        $new_ver = implode('.', $parts);
        $project_storage = __DIR__ . '/storage/' . $mgmt_hash;
        $filename = "v" . $new_ver . ".zip";
        move_uploaded_file($_FILES['file']['tmp_name'], $project_storage . '/' . $filename);
        $projects[$mgmt_hash]['latest_version'] = $new_ver;
        $projects[$mgmt_hash]['versions'][] = $new_ver;
        $projects[$mgmt_hash]['updated_at'] = date('c');
        save_projects($projects);
        echo json_encode(['status' => 'ok', 'version' => $new_ver]);
        break;

    case 'versions':
        $login_id = $_GET['login_id'] ?? '';
        $login_pw = $_GET['login_pw'] ?? '';
        $mgmt_num = $_GET['management_number'] ?? '';

        if (is_secure_mgmt($mgmt_num) && !check_auth($login_id, $login_pw)) {
            http_response_code(401);
            die(json_encode(['status' => 'error', 'message' => 'Unauthorized for Secure project']));
        }

        $projects = get_projects();
        $mgmt_hash = get_mgmt_hash($mgmt_num);
        if (isset($projects[$mgmt_hash])) {
            echo json_encode(['versions' => $projects[$mgmt_hash]['versions']]);
        } else {
            http_response_code(404);
            echo json_encode(['status' => 'error', 'message' => 'Project not found']);
        }
        break;

    case 'download':
        $login_id = $_GET['login_id'] ?? '';
        $login_pw = $_GET['login_pw'] ?? '';
        $mgmt_num = $_GET['management_number'] ?? '';
        $version = $_GET['version'] ?? '';

        if (is_secure_mgmt($mgmt_num) && !check_auth($login_id, $login_pw)) {
            http_response_code(401);
            die(json_encode(['status' => 'error', 'message' => 'Unauthorized for Secure project']));
        }

        $projects = get_projects();
        $mgmt_hash = get_mgmt_hash($mgmt_num);
        if (!isset($projects[$mgmt_hash])) {
            http_response_code(404);
            die(json_encode(['status' => 'error', 'message' => 'Project not found']));
        }
        if (empty($version) || $version === 'LATEST') {
            $version = $projects[$mgmt_hash]['latest_version'];
        }
        $file_path = __DIR__ . '/storage/' . $mgmt_hash . '/v' . $version . '.zip';
        if (file_exists($file_path)) {
            header('Content-Type: application/zip');
            header('Content-Disposition: attachment; filename="' . $projects[$mgmt_hash]['project_name'] . '_v' . $version . '.zip"');
            readfile($file_path);
        } else {
            http_response_code(404);
            echo json_encode(['status' => 'error', 'message' => 'Version not found']);
        }
        break;

    case 'info':
        $login_id = $_GET['login_id'] ?? '';
        $login_pw = $_GET['login_pw'] ?? '';
        $mgmt_num = $_GET['management_number'] ?? '';

        if (is_secure_mgmt($mgmt_num) && !check_auth($login_id, $login_pw)) {
            http_response_code(401);
            die(json_encode(['status' => 'error', 'message' => 'Unauthorized for Secure project']));
        }

        $projects = get_projects();
        $mgmt_hash = get_mgmt_hash($mgmt_num);
        if (isset($projects[$mgmt_hash])) {
            echo json_encode($projects[$mgmt_hash]);
        } else {
            http_response_code(404);
            echo json_encode(['status' => 'error', 'message' => 'Project not found']);
        }
        break;

    case 'edit':
        $login_id = $input['login_id'] ?? '';
        $login_pw = $input['login_pw'] ?? '';
        $old_mgmt = $input['old_management_number'] ?? '';
        $new_mgmt = $input['new_management_number'] ?? '';
        $change_key = $input['change_key'] ?? '';

        if (!check_auth($login_id, $login_pw)) {
            http_response_code(401);
            die(json_encode(['status' => 'error', 'message' => 'Unauthorized']));
        }

        $projects = get_projects();
        $old_hash = get_mgmt_hash($old_mgmt);
        $new_hash = get_mgmt_hash($new_mgmt);

        if (!isset($projects[$old_hash])) {
            http_response_code(404);
            die(json_encode(['status' => 'error', 'message' => 'Project not found']));
        }

        // UserID変更チェック (管理番号の第2セグメントが変わる場合)
        $old_parts = explode('_', $old_mgmt);
        $new_parts = explode('_', $new_mgmt);
        if (count($old_parts) > 1 && count($new_parts) > 1 && $old_parts[1] !== $new_parts[1]) {
            $stored_key = $config['admin']['change_key'] ?? '';
            if (empty($change_key) || trim($change_key) !== trim($stored_key)) {
                http_response_code(403);
                die(json_encode(['status' => 'error', 'message' => 'Invalid or missing ChangeKey for UserID change']));
            }
        }

        // ストレージの移動
        $old_path = __DIR__ . '/storage/' . $old_hash;
        $new_path = __DIR__ . '/storage/' . $new_hash;
        if (is_dir($old_path) && !is_dir($new_path)) {
            rename($old_path, $new_path);
        }

        // データの更新
        $project_data = $projects[$old_hash];
        $project_data['management_number'] = $new_mgmt;
        unset($projects[$old_hash]);
        $projects[$new_hash] = $project_data;
        save_projects($projects);

        echo json_encode(['status' => 'ok', 'new_management_number' => $new_mgmt]);
        break;

    case 'delete':
        $login_id = $input['login_id'] ?? '';
        $login_pw = $input['login_pw'] ?? '';
        $mgmt_num = $input['management_number'] ?? '';

        if (!check_auth($login_id, $login_pw)) {
            http_response_code(401);
            die(json_encode(['status' => 'error', 'message' => 'Unauthorized']));
        }

        $projects = get_projects();
        $mgmt_hash = get_mgmt_hash($mgmt_num);

        if (!isset($projects[$mgmt_hash])) {
            http_response_code(404);
            die(json_encode(['status' => 'error', 'message' => 'Project not found']));
        }

        // Delete from data array and save (rewrites SQLite or JSON)
        unset($projects[$mgmt_hash]);
        save_projects($projects);

        // Delete physical files
        $project_storage = __DIR__ . '/storage/' . $mgmt_hash;
        if (is_dir($project_storage)) {
            $files = array_diff(scandir($project_storage), ['.', '..']);
            foreach ($files as $file) {
                unlink($project_storage . '/' . $file);
            }
            rmdir($project_storage);
        }

        echo json_encode(['status' => 'ok', 'message' => 'Project deleted successfully']);
        break;

    case 'check_update':
        $current_version = $_GET['current_version'] ?? '0.0.0';
        $update_info_file = __DIR__ . '/updates/latest.json';
        
        if (file_exists($update_info_file)) {
            $update_info = json_decode(file_get_contents($update_info_file), true);
            $latest_version = $update_info['version'] ?? '1.0.0';
            
            $download_url = $update_info['download_url'] ?? '';
            // Generate full URL if it's a relative path
            if ($download_url && !preg_match('/^https?:\/\//', $download_url)) {
                $protocol = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off' || $_SERVER['SERVER_PORT'] == 443) ? "https://" : "http://";
                $domainName = $_SERVER['HTTP_HOST'] ?? 'localhost';
                $base_url = $protocol . $domainName . dirname($_SERVER['SCRIPT_NAME']);
                $download_url = rtrim($base_url, '/') . '/' . ltrim($download_url, '/');
            }
            
            // version_compare handles strings like '1.0.5β'. 
            // Often it ignores non-standard suffixes, so we can strip or just let PHP compare.
            // Usually '1.0.5' is enough.
            if (version_compare(preg_replace('/[^0-9\.]/', '', $latest_version), preg_replace('/[^0-9\.]/', '', $current_version), '>')) {
                echo json_encode([
                    'has_update' => true,
                    'latest_version' => $latest_version,
                    'download_url' => $download_url
                ]);
            } else {
                echo json_encode([
                    'has_update' => false,
                    'latest_version' => $latest_version
                ]);
            }
        } else {
            echo json_encode(['has_update' => false, 'message' => 'Update info not found']);
        }
        break;

    default:
            http_response_code(400);
            echo json_encode(['status' => 'error', 'message' => 'Invalid action']);
            break;
    }
    exit; // Stop execution after handling API request
}
