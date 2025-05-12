// Biến toàn cục cho Three.js
let scene, camera, renderer, controls;
let tubeGroup; // Một nhóm để chứa tất cả các đoạn ống, dễ dàng xóa và thêm lại

// Màu sắc cho các đoạn ống
const STRAIGHT_SEGMENT_COLOR = 0x007bff; // Màu xanh dương cho đoạn thẳng (Y)
const BENT_SEGMENT_COLOR = 0xff4500;    // Màu cam đỏ cho đoạn cong (B)
const DEFAULT_TUBE_COLOR = 0xcccccc;   // Màu xám nếu không xác định được loại

// Khởi tạo môi trường 3D (Tương tự như trước)
function init3DViewer() {
    const container = document.getElementById('viewerContainer');
    if (!container) {
        console.error("Không tìm thấy 'viewerContainer'.");
        return;
    }

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);

    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 20000);
    camera.position.set(100, 150, 250);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(150, 200, 100);
    scene.add(directionalLight);

    const axesHelper = new THREE.AxesHelper(100);
    scene.add(axesHelper);
    const gridHelper = new THREE.GridHelper(500, 20, 0xcccccc, 0xdddddd);
    scene.add(gridHelper);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = true;
    controls.target.set(0, 50, 0);

    tubeGroup = new THREE.Group();
    scene.add(tubeGroup);

    window.addEventListener('resize', onWindowResize, false);
    onWindowResize();
    animate();
}

function onWindowResize() {
    const container = document.getElementById('viewerContainer');
    if (!container || !renderer || !camera) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

function showMessage(message, type = 'error') {
    const messageArea = document.getElementById('messageArea');
    if (!messageArea) return;
    messageArea.innerHTML = '';
    const messageDiv = document.createElement('div');
    messageDiv.textContent = message;
    messageDiv.className = type === 'error' ? 'error-message' : 'success-message';
    messageArea.appendChild(messageDiv);
}

// ---- CÁC HÀM MỚI VÀ CẬP NHẬT CHO GIAO DIỆN BẢNG VÀ BIÊN DẠNG ----

// Cập nhật hiển thị các ô nhập kích thước dựa trên loại biên dạng được chọn
function updateProfileOptionsVisibility() {
    const profileType = document.getElementById('profileType').value;
    document.getElementById('roundProfileOptions').style.display = profileType === 'round' ? 'block' : 'none';
    document.getElementById('squareProfileOptions').style.display = profileType === 'square' ? 'block' : 'none';
    document.getElementById('rectangleProfileOptions').style.display = profileType === 'rectangle' ? 'block' : 'none';
}

// Thêm một dòng mới vào bảng YBCR
function addRowToTable() {
    const tableBody = document.getElementById('ybcrTableBody');
    const newRow = tableBody.insertRow(); // Thêm vào cuối bảng

    newRow.innerHTML = `
        <td><input type="checkbox" name="selectRow"></td>
        <td><input type="number" class="y-input" value="0"></td>
        <td><input type="number" class="b-input" value="0"></td>
        <td><input type="number" class="c-input" value="0"></td>
        <td><input type="number" class="r-input" value="0"></td>
    `;
}

// Xóa các dòng được chọn trong bảng YBCR
function deleteSelectedRows() {
    const tableBody = document.getElementById('ybcrTableBody');
    const checkboxes = tableBody.querySelectorAll('input[type="checkbox"][name="selectRow"]:checked');
    checkboxes.forEach(checkbox => {
        tableBody.removeChild(checkbox.closest('tr'));
    });
    if (checkboxes.length === 0) {
        showMessage("Vui lòng chọn ít nhất một dòng để xóa.", "error");
    } else {
        showMessage(`${checkboxes.length} dòng đã được xóa.`, "success");
    }
}


// Hàm vẽ biên dạng (thay thế hàm drawTube cũ)
function drawProfileGeometry(centerlinePoints, segmentInfo, profileData) {
    // Xóa các đối tượng cũ trong group
    while (tubeGroup.children.length > 0) {
        const oldSegment = tubeGroup.children[0];
        tubeGroup.remove(oldSegment);
        if (oldSegment.geometry) oldSegment.geometry.dispose();
        if (oldSegment.material) oldSegment.material.dispose();
    }

    if (!centerlinePoints || centerlinePoints.length < 2 || !profileData) {
        showMessage("Dữ liệu không đủ hoặc không hợp lệ để vẽ biên dạng.");
        console.error("Dữ liệu không đủ:", { centerlinePoints, profileData });
        return;
    }
    showMessage("Đang tạo biên dạng 3D...", "success");

    const { type, dimensions } = profileData;

    // Tham số chung cho TubeGeometry và ExtrudeGeometry
    const radiusSegmentsTube = 12; // Cho ống tròn
    const closedTube = false;

    // Tham số cho ExtrudeGeometry
    const extrudeSettings = {
        steps: 64, // Số bước dọc theo đường dẫn, có thể tăng để mượt hơn
        bevelEnabled: false,
        extrudePath: null // Sẽ được gán cho từng đoạn
    };

    if (!segmentInfo || segmentInfo.length === 0) {
        // Trường hợp không có segmentInfo (ít khi xảy ra nếu backend hoạt động đúng)
        // Vẽ toàn bộ đường tâm bằng một hình học duy nhất
        console.warn("Không có thông tin segmentInfo, vẽ toàn bộ đường bằng một hình học.");
        const pointsVec3 = centerlinePoints.map(p => new THREE.Vector3(p[0], p[1], p[2]));
        if (pointsVec3.length < 2) {
             showMessage("Cần ít nhất 2 điểm để vẽ đường."); return;
        }
        const path = new THREE.CatmullRomCurve3(pointsVec3);
        let geometry;
        const material = new THREE.MeshPhongMaterial({ color: DEFAULT_TUBE_COLOR, side: THREE.DoubleSide });

        if (type === 'round') {
            geometry = new THREE.TubeGeometry(path, Math.max(64, pointsVec3.length * 5), dimensions.diameter / 2, radiusSegmentsTube, closedTube);
        } else {
            let shape;
            if (type === 'square') {
                const s = dimensions.side;
                shape = new THREE.Shape();
                shape.moveTo(-s / 2, -s / 2);
                shape.lineTo(s / 2, -s / 2);
                shape.lineTo(s / 2, s / 2);
                shape.lineTo(-s / 2, s / 2);
                shape.closePath();
            } else if (type === 'rectangle') {
                const w = dimensions.width;
                const h = dimensions.height;
                shape = new THREE.Shape();
                shape.moveTo(-w / 2, -h / 2);
                shape.lineTo(w / 2, -h / 2);
                shape.lineTo(w / 2, h / 2);
                shape.lineTo(-w / 2, h / 2);
                shape.closePath();
            }
            if (shape) {
                extrudeSettings.extrudePath = path;
                geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
            }
        }
        if (geometry) {
            const mesh = new THREE.Mesh(geometry, material);
            tubeGroup.add(mesh);
        }
    } else {
        // Vẽ từng đoạn ống với màu và hình dạng tương ứng
        segmentInfo.forEach(segment => {
            const segmentPoints = [];
            for (let i = segment.start_idx; i <= segment.end_idx; i++) {
                if (centerlinePoints[i]) {
                    segmentPoints.push(new THREE.Vector3(centerlinePoints[i][0], centerlinePoints[i][1], centerlinePoints[i][2]));
                }
            }

            if (segmentPoints.length < 2) {
                console.warn("Đoạn biên dạng không đủ điểm để vẽ:", segment);
                return;
            }

            const path = new THREE.CatmullRomCurve3(segmentPoints);
            let geometry;
            let segmentColor = DEFAULT_TUBE_COLOR;
            if (segment.type === 'Y') segmentColor = STRAIGHT_SEGMENT_COLOR;
            else if (segment.type === 'B') segmentColor = BENT_SEGMENT_COLOR;
            
            const material = new THREE.MeshPhongMaterial({ color: segmentColor, side: THREE.DoubleSide });

            if (type === 'round') {
                const tubeRadius = dimensions.diameter / 2;
                geometry = new THREE.TubeGeometry(path, Math.max(20, segmentPoints.length * 5), tubeRadius, radiusSegmentsTube, closedTube);
            } else {
                let shape;
                if (type === 'square') {
                    const s = dimensions.side;
                    shape = new THREE.Shape();
                    // Vẽ hình vuông đối xứng quanh gốc tọa độ
                    shape.moveTo(-s / 2, -s / 2); shape.lineTo(s / 2, -s / 2);
                    shape.lineTo(s / 2, s / 2); shape.lineTo(-s / 2, s / 2);
                    shape.closePath();
                } else if (type === 'rectangle') {
                    const w = dimensions.width;
                    const h = dimensions.height;
                    shape = new THREE.Shape();
                    shape.moveTo(-w / 2, -h / 2); shape.lineTo(w / 2, -h / 2);
                    shape.lineTo(w / 2, h / 2); shape.lineTo(-w / 2, h / 2);
                    shape.closePath();
                }

                if (shape) {
                    const currentExtrudeSettings = { ...extrudeSettings }; // Sao chép để không thay đổi object gốc
                    currentExtrudeSettings.extrudePath = path;
                    currentExtrudeSettings.steps = Math.max(20, segmentPoints.length * 5); // Điều chỉnh steps cho từng đoạn
                    
                    // QUAN TRỌNG: Định hướng của ExtrudeGeometry
                    // Three.js sẽ cố gắng tính toán Frenet frames.
                    // Để có định hướng chính xác hơn, đặc biệt sau các phép xoay C,
                    // backend lý tưởng nên cung cấp vector "up" (hoặc pháp tuyến của mặt phẳng uốn)
                    // cho mỗi điểm trên đường tâm. Sau đó, có thể dùng THREE.Path.getSpacedPoints()
                    // cùng với các vector up đó để tạo custom frames cho extrudeSettings.frames.
                    // Hiện tại, chúng ta dựa vào tính toán mặc định của Three.js.
                    geometry = new THREE.ExtrudeGeometry(shape, currentExtrudeSettings);
                }
            }

            if (geometry) {
                const mesh = new THREE.Mesh(geometry, material);
                tubeGroup.add(mesh);
            }
        });
    }
    
    // Tự động điều chỉnh camera (giữ nguyên logic)
    if (tubeGroup.children.length > 0) {
        const boundingBox = new THREE.Box3().setFromObject(tubeGroup);
        const center = new THREE.Vector3();
        const size = new THREE.Vector3();
        boundingBox.getCenter(center);
        boundingBox.getSize(size);

        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = camera.fov * (Math.PI / 180);
        let cameraDistance = Math.abs(maxDim / 2 / Math.tan(fov / 2));
        cameraDistance *= 1.8; 

        const direction = new THREE.Vector3();
        camera.getWorldDirection(direction);
        camera.position.copy(center).addScaledVector(direction.multiplyScalar(-1), cameraDistance);
        if (camera.position.y < size.y * 0.2 + center.y) {
            camera.position.y = size.y * 0.2 + center.y + 20;
        }
        controls.target.copy(center);
        controls.update();
        showMessage("Tạo biên dạng 3D thành công!", "success");
    } else {
        showMessage("Không có gì để vẽ hoặc dữ liệu không hợp lệ.", "error");
    }
}


// Hàm xử lý khi nhấn nút "Tạo Biên Dạng 3D"
async function handleGenerateTube() {
    const profileType = document.getElementById('profileType').value;
    let profileDimensions = {};
    let isValidDimensions = true;

    // Thu thập kích thước dựa trên loại biên dạng
    if (profileType === 'round') {
        const diameter = parseFloat(document.getElementById('diameter').value);
        if (isNaN(diameter) || diameter <= 0) {
            showMessage("Vui lòng nhập đường kính hợp lệ (số dương).");
            isValidDimensions = false;
        } else {
            profileDimensions.diameter = diameter;
        }
    } else if (profileType === 'square') {
        const side = parseFloat(document.getElementById('squareSide').value);
        if (isNaN(side) || side <= 0) {
            showMessage("Vui lòng nhập cạnh hình vuông hợp lệ (số dương).");
            isValidDimensions = false;
        } else {
            profileDimensions.side = side;
        }
    } else if (profileType === 'rectangle') {
        const width = parseFloat(document.getElementById('rectWidth').value);
        const height = parseFloat(document.getElementById('rectHeight').value);
        if (isNaN(width) || width <= 0 || isNaN(height) || height <= 0) {
            showMessage("Vui lòng nhập chiều rộng và chiều cao hình chữ nhật hợp lệ (số dương).");
            isValidDimensions = false;
        } else {
            profileDimensions.width = width;
            profileDimensions.height = height;
        }
    }
    if (!isValidDimensions) return;

    // Thu thập dữ liệu từ bảng YBCR
    const ybcrTableBody = document.getElementById('ybcrTableBody');
    const rows = ybcrTableBody.querySelectorAll('tr');
    const ybcrData = [];
    let tableDataValid = true;

    rows.forEach((row, index) => {
        const yInput = row.querySelector('.y-input');
        const bInput = row.querySelector('.b-input');
        const cInput = row.querySelector('.c-input');
        const rInput = row.querySelector('.r-input');

        if (yInput && bInput && cInput && rInput) {
            const y = parseFloat(yInput.value);
            const b = parseFloat(bInput.value);
            const c = parseFloat(cInput.value);
            const r = parseFloat(rInput.value);

            if (isNaN(y) || isNaN(b) || isNaN(c) || isNaN(r)) {
                showMessage(`Dữ liệu không hợp lệ ở dòng ${index + 1} trong bảng YBCR.`);
                tableDataValid = false;
                return; // Dừng forEach nếu có lỗi
            }
            // Kiểm tra Radius không âm (nếu cần, backend cũng có kiểm tra này)
            if (r < 0) {
                showMessage(`Radius không thể âm ở dòng ${index + 1}.`);
                tableDataValid = false;
                return;
            }
            ybcrData.push({ Y: y, B: b, C: c, Radius: r });
        }
    });

    if (!tableDataValid) return;
    if (ybcrData.length === 0) {
        showMessage("Vui lòng thêm ít nhất một dòng dữ liệu YBCR.");
        return;
    }

    const payload = {
        profile: { // Gửi thông tin biên dạng trong một object 'profile'
            type: profileType,
            dimensions: profileDimensions
        },
        YBC: ybcrData
        // NumArcPoints: 30 // Có thể thêm nếu muốn tùy chỉnh
    };

    showMessage("Đang gửi dữ liệu đến server...", "success");

    try {
        const response = await fetch('http://127.0.0.1:5000/api/calculate_tube', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const result = await response.json();

        if (!response.ok) {
            const errorMessage = result.error || `Lỗi HTTP: ${response.status} ${response.statusText}`;
            throw new Error(errorMessage);
        }
        if (result.error) {
            throw new Error(result.error);
        }

        // Backend nên trả về cả centerline_points, segment_info, và profile (để xác nhận)
        if (result.centerline_points && result.segment_info && result.profile) {
            drawProfileGeometry(result.centerline_points, result.segment_info, result.profile);
        } else {
            console.error("Kết quả từ server không hợp lệ:", result);
            showMessage("Kết quả từ server không chứa đủ thông tin (centerline_points, segment_info, profile).");
        }

    } catch (error) {
        console.error('Lỗi khi gửi yêu cầu hoặc xử lý kết quả:', error);
        showMessage('Không thể tạo biên dạng: ' + error.message, 'error');
        while (tubeGroup.children.length > 0) { // Xóa hình cũ nếu lỗi
            const oldSegment = tubeGroup.children[0];
            tubeGroup.remove(oldSegment);
            if (oldSegment.geometry) oldSegment.geometry.dispose();
            if (oldSegment.material) oldSegment.material.dispose();
        }
    }
}

// Gán sự kiện và khởi tạo
window.onload = () => {
    init3DViewer();

    // Xử lý thay đổi loại biên dạng
    const profileTypeSelect = document.getElementById('profileType');
    if (profileTypeSelect) {
        profileTypeSelect.addEventListener('change', updateProfileOptionsVisibility);
        updateProfileOptionsVisibility(); // Gọi lần đầu để hiển thị đúng ô input
    }

    // Nút thêm dòng
    const addRowButton = document.getElementById('addRowButton');
    if (addRowButton) {
        addRowButton.addEventListener('click', addRowToTable);
    }

    // Nút xóa dòng
    const deleteSelectedRowButton = document.getElementById('deleteSelectedRowButton');
    if (deleteSelectedRowButton) {
        deleteSelectedRowButton.addEventListener('click', deleteSelectedRows);
    }
    
    // Nút Generate
    const generateButton = document.getElementById('generateButton');
    if (generateButton) {
        generateButton.addEventListener('click', handleGenerateTube);
    }
};
