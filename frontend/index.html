<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trực Quan Hóa Ống Cong 3D - Đa Biên Dạng</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            background-color: #f3f4f6;
            margin: 0;
            padding-top: 1rem;
            padding-bottom: 1rem; /* Thêm padding dưới để tránh nút Generate bị che khi cuộn */
        }
        .main-container {
            display: flex;
            flex-direction: row;
            gap: 1rem;
            width: 95%;
            max-width: 1600px;
            /* Loại bỏ height cố định để nội dung có thể mở rộng */
            /* height: calc(100vh - 4rem); */
            background-color: white;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            overflow: hidden;
        }
        #controlsPanel {
            width: 40%;
            min-width: 320px; /* Giảm min-width cho màn hình nhỏ hơn */
            padding: 1.5rem;
            background-color: #ffffff;
            border-right: 1px solid #e5e7eb;
            overflow-y: auto; /* Cho phép cuộn panel điều khiển nếu nội dung dài */
            display: flex;
            flex-direction: column;
            /* Giới hạn chiều cao tối đa cho panel control, đặc biệt quan trọng trên mobile */
            max-height: calc(100vh - 2rem); /* Để chừa không gian cho padding body */
        }
        #viewerContainer {
            width: 60%;
            height: calc(100vh - 2rem); /* Giữ chiều cao viewer */
            min-height: 300px; /* Chiều cao tối thiểu cho viewer */
            position: relative;
        }
        label {
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: #374151;
            display: block;
        }
        input[type="number"], select {
            width: 100%;
            padding: 0.5rem 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
            box-sizing: border-box;
            transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        input[type="number"]:focus, select:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
            outline: none;
        }
        .profile-options div {
            margin-bottom: 1rem;
        }
        .profile-options label {
            font-size: 0.875rem;
            margin-bottom: 0.25rem;
        }
        .profile-options input[type="number"] {
            margin-bottom: 0.5rem;
        }

        #generateButton {
            background-color: #16a34a;
            color: white;
            font-weight: 700;
            padding: 0.875rem 2rem;
            border: none;
            border-radius: 0.375rem;
            cursor: pointer;
            transition: background-color 0.2s ease-in-out;
            margin-top: 1.5rem;
            font-size: 1.125rem;
            width: 100%;
        }
        #generateButton:hover {
            background-color: #15803d;
        }
        .action-buttons button {
            background-color: #4f46e5;
            color: white;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 0.375rem;
            cursor: pointer;
            transition: background-color 0.2s ease-in-out;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem; /* Thêm margin bottom cho nút trên mobile */
        }
        .action-buttons button.delete-button {
            background-color: #dc2626;
        }
        .action-buttons button:hover {
            opacity: 0.85;
        }

        /* === CẬP NHẬT CSS CHO BẢNG YBCR === */
        #ybcrTableContainer {
            margin-top: 1rem;
            /* Cho phép cuộn ngang và dọc */
            overflow: auto; /* Thay đổi từ overflow-y: auto */
            border: 1px solid #e5e7eb;
            border-radius: 0.375rem;
            flex-grow: 1; /* Cho phép bảng mở rộng */
            /* Giới hạn chiều cao tối đa để không làm panel quá dài */
            max-height: 300px; 
        }
        #ybcrTable {
            width: 100%;
            min-width: 500px; /* Đặt chiều rộng tối thiểu cho bảng để nó không bị bóp quá mức */
            border-collapse: collapse;
        }
        #ybcrTable th, #ybcrTable td {
            border: 1px solid #e5e7eb;
            padding: 0.5rem; /* Có thể giảm padding nếu cần */
            text-align: center;
            font-size: 0.875rem;
            /* Đảm bảo các ô không bị co lại quá mức */
            white-space: nowrap; 
        }
        #ybcrTable th {
            background-color: #f9fafb;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10; /* Đảm bảo header nổi lên trên khi cuộn */
        }
        #ybcrTable td input[type="number"] {
            /* Giảm chiều rộng một chút để vừa hơn trên mobile, nhưng vẫn đủ dùng */
            width: 70px; 
            min-width: 60px; /* Chiều rộng tối thiểu */
            padding: 0.35rem 0.4rem; /* Giảm padding của input */
            margin-bottom: 0;
            text-align: right;
            font-size: 0.875rem; /* Đồng bộ font size */
        }
        #ybcrTable td input[type="checkbox"] {
            margin: 0 auto;
            display: block;
            /* Tăng kích thước checkbox để dễ chạm hơn */
            width: 1.15rem; 
            height: 1.15rem;
        }
        /* === KẾT THÚC CẬP NHẬT CSS CHO BẢNG YBCR === */

        .error-message, .success-message {
            color: #ef4444;
            background-color: #fee2e2;
            border: 1px solid #fca5a5;
            padding: 0.75rem;
            border-radius: 0.375rem;
            margin-top: 1rem;
            font-size: 0.875rem;
        }
        .success-message {
            color: #166534;
            background-color: #dcfce7;
            border: 1px solid #86efac;
        }
        h1 {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        /* Responsive adjustments */
        @media (max-width: 900px) { /* Giữ nguyên breakpoint này hoặc điều chỉnh nếu cần */
            .main-container {
                flex-direction: column;
                height: auto; /* Cho phép chiều cao tự điều chỉnh */
                width: 100%; /* Chiếm toàn bộ chiều rộng màn hình */
                border-radius: 0; /* Bỏ bo góc trên mobile nếu muốn */
            }
            #controlsPanel {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid #e5e7eb; /* Thêm đường kẻ dưới khi xếp dọc */
                max-height: none; /* Bỏ giới hạn chiều cao panel control khi xếp dọc để có thể cuộn toàn trang */
                /* Hoặc đặt một max-height phù hợp cho mobile, ví dụ 50vh hoặc 60vh */
                /* max-height: 60vh; */ 
                overflow-y: auto; /* Đảm bảo panel control vẫn cuộn được nếu nội dung dài */
            }
            #viewerContainer {
                width: 100%;
                height: 50vh; /* Chiều cao cố định cho viewer trên mobile */
                min-height: 300px;
            }
            /* Điều chỉnh cho bảng trên màn hình nhỏ hơn nữa nếu cần */
            #ybcrTable th, #ybcrTable td {
                padding: 0.4rem; /* Giảm padding thêm chút nữa */
                font-size: 0.8rem; /* Giảm font size thêm chút nữa */
            }
            #ybcrTable td input[type="number"] {
                width: 60px;
                font-size: 0.8rem;
            }
        }
        /* Thêm breakpoint cho màn hình rất nhỏ nếu bảng vẫn bị che */
        @media (max-width: 480px) {
            #ybcrTable th, #ybcrTable td {
                padding: 0.3rem;
                font-size: 0.75rem;
            }
             #ybcrTable td input[type="number"] {
                width: 50px; /* Giảm chiều rộng input cho màn hình rất nhỏ */
                min-width: 45px;
                font-size: 0.75rem;
            }
            .action-buttons {
                display: flex;
                flex-direction: column; /* Xếp các nút Thêm/Xóa dọc */
                gap: 0.5rem;
            }
            .action-buttons button {
                width: 100%;
                margin-right: 0;
            }
            h1 {
                font-size: 1.25rem; /* Giảm kích thước tiêu đề chính */
            }
        }

        /* Ẩn các tùy chọn kích thước biên dạng ban đầu */
        .profile-dimension-options {
            display: none;
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div id="controlsPanel">
            <h1>YBCR Data Input</h1>

            <label for="profileType">Shape type</label>
            <select id="profileType" class="rounded-md shadow-sm">
                <option value="round" selected>Round tube</option>
                <option value="square">Square</option>
                <option value="rectangle">Rectangle</option>
            </select>

            <div id="profileOptionsContainer" class="mt-2">
                <div id="roundProfileOptions" class="profile-dimension-options">
                    <label for="diameter">Đường kính ống (mm):</label>
                    <input type="number" id="diameter" value="30" class="rounded-md shadow-sm">
                </div>
                <div id="squareProfileOptions" class="profile-dimension-options">
                    <label for="squareSide">Cạnh hình vuông (mm):</label>
                    <input type="number" id="squareSide" value="20" class="rounded-md shadow-sm">
                </div>
                <div id="rectangleProfileOptions" class="profile-dimension-options">
                    <label for="rectWidth">Chiều rộng hình chữ nhật (mm):</label>
                    <input type="number" id="rectWidth" value="30" class="rounded-md shadow-sm">
                    <label for="rectHeight">Chiều cao hình chữ nhật (mm):</label>
                    <input type="number" id="rectHeight" value="20" class="rounded-md shadow-sm">
                </div>
            </div>

            <h2 class="text-lg font-semibold mt-4 mb-2 text-gray-700">YBCRadius:</h2>
            <div class="action-buttons mb-3">
                <button id="addRowButton">Add bend</button>
                <button id="deleteSelectedRowButton" class="delete-button">Delete bend</button>
            </div>

            <div id="ybcrTableContainer">
                <table id="ybcrTable">
                    <thead>
                        <tr>
                            <th>select</th>
                            <th>Y (Feed)</th>
                            <th>B (Bend °)</th>
                            <th>C (Rotation °)</th>
                            <th>Radius</th>
                        </tr>
                    </thead>
                    <tbody id="ybcrTableBody">
                        <tr>
                            <td><input type="checkbox" name="selectRow"></td>
                            <td><input type="number" class="y-input" value="100"></td>
                            <td><input type="number" class="b-input" value="90"></td>
                            <td><input type="number" class="c-input" value="0"></td>
                            <td><input type="number" class="r-input" value="50"></td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <button id="generateButton">View 3D shape</button>
            <div id="messageArea" class="mt-4"></div>
        </div>

        <div id="viewerContainer">
            </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="main.js"></script>
</body>
</html>
