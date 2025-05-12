import math
import numpy as np
import json
import sys # Vẫn cần thiết để ghi log lỗi ra stderr

# --- Hàm phụ trợ --- (Giữ nguyên)
def rotate_vector(vector, axis, angle_rad):
    """ Quay vector quanh trục bằng công thức Rodrigues """
    vector = np.asarray(vector, dtype=float)
    axis = np.asarray(axis, dtype=float)
    norm_axis = np.linalg.norm(axis)
    if norm_axis < 1e-9: # Tránh chia cho 0 nếu trục là zero vector
        # print("Warning: Zero norm axis in rotate_vector. Returning original vector.", file=sys.stderr)
        return vector
    axis = axis / norm_axis
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    # Công thức Rodrigues
    result = vector * cos_a + np.cross(axis, vector) * sin_a + axis * np.dot(axis, vector) * (1 - cos_a)
    return np.asarray(result, dtype=float)

# --- Hàm chính đã được chỉnh sửa để phù hợp với môi trường web ---
def calculate_centerline_from_data(data_dict):
    """
    Tính toán đường tâm ống từ dictionary dữ liệu YBCR.
    data_dict: một dictionary chứa 'Diameter' (tùy chọn) và 'YBC' (bắt buộc).
    Trả về một chuỗi JSON chứa kết quả hoặc thông tin lỗi.
    """
    tube_diameter = 30.0  # Giá trị mặc định
    error_response_template = {
        "error": "",
        "centerline_points": [], "segment_info": [],
        "final_point": [0,0,0], "final_direction": [1,0,0], # Giá trị mặc định an toàn
        "diameter": tube_diameter
    }

    # 1. Đọc và kiểm tra dữ liệu đầu vào từ data_dict
    if not isinstance(data_dict, dict):
        print("ERROR: Input data_dict is not a dictionary.", file=sys.stderr)
        error_response = error_response_template.copy()
        error_response["error"] = "Dữ liệu đầu vào không hợp lệ (không phải dictionary)."
        return json.dumps(error_response, separators=(',', ':'))

    # Đọc Diameter
    try:
        diameter_from_input = data_dict.get('Diameter') # Dùng get để tránh KeyError nếu không có
        if diameter_from_input is not None: # Chỉ xử lý nếu 'Diameter' được cung cấp
            if isinstance(diameter_from_input, (int, float)):
                if float(diameter_from_input) > 0:
                    tube_diameter = float(diameter_from_input)
                    print(f"INFO: Đọc Diameter từ input: {tube_diameter}", file=sys.stderr)
                else:
                    print(f"WARNING: Diameter '{diameter_from_input}' không hợp lệ (<=0), dùng mặc định: {tube_diameter}", file=sys.stderr)
            else:
                print(f"WARNING: Giá trị Diameter '{diameter_from_input}' không phải là số, dùng mặc định: {tube_diameter}", file=sys.stderr)
        else:
            print(f"INFO: Key 'Diameter' không tìm thấy trong input. Dùng mặc định: {tube_diameter}", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Lỗi khi xử lý Diameter từ input, dùng mặc định: {tube_diameter}. Error: {e}", file=sys.stderr)
        # tube_diameter đã có giá trị mặc định, không cần gán lại

    error_response_template["diameter"] = tube_diameter # Cập nhật diameter cho template lỗi

    # Kiểm tra key 'YBC'
    if 'YBC' not in data_dict or not isinstance(data_dict['YBC'], list):
        print("ERROR: Input data_dict thiếu key 'YBC' hoặc 'YBC' không phải là một list.", file=sys.stderr)
        error_response = error_response_template.copy()
        error_response["error"] = "Dữ liệu đầu vào không đúng cấu trúc (thiếu 'YBC' hoặc 'YBC' không phải list)."
        return json.dumps(error_response, separators=(',', ':'))

    bend_data = data_dict['YBC']
    print(f"INFO: Đọc {len(bend_data)} dòng YBC từ input data", file=sys.stderr)

    if not bend_data and len(bend_data) == 0: # Xử lý trường hợp list YBC rỗng
        print("INFO: Danh sách 'YBC' rỗng. Trả về kết quả rỗng.", file=sys.stderr)
        # Vẫn trả về cấu trúc hợp lệ với các mảng rỗng và giá trị mặc định
        empty_output = {
            "centerline_points": [], "segment_info": [],
            "final_point": [0,0,0], "final_direction": [1,0,0],
            "diameter": tube_diameter
        }
        return json.dumps(empty_output, separators=(',', ':'))


    # 2. Khởi tạo trạng thái và danh sách kết quả (Giống code gốc)
    current_point = np.array([0.0, 0.0, 0.0])
    current_direction = np.array([1.0, 0.0, 0.0]) # Hướng ban đầu dọc theo trục X
    current_up_vector = np.array([0.0, 0.0, 1.0]) # Vector Up ban đầu dọc theo trục Z (xác định mặt phẳng uốn ban đầu XY)
    centerline_points_forward = [current_point.copy()]
    segment_details = []
    start_idx_for_segment = 0
    num_arc_points = data_dict.get('NumArcPoints', 30) # Cho phép tùy chỉnh số điểm trên cung, mặc định 30

    print("\n--- Bắt đầu tính toán (Sequence: Feed -> Bend -> Rotate) ---", file=sys.stderr)

    # 3. Vòng lặp xử lý YBCR
    for i, bend_props in enumerate(bend_data):
        try:
            y = float(bend_props['Y'])
            b_deg = float(bend_props['B'])
            c_deg = float(bend_props['C'])
            r = float(bend_props.get('Radius', 0.0)) # Dùng get với giá trị mặc định 0 nếu Radius có thể thiếu
            if r < 0:
                # Quyết định xử lý R < 0: coi là lỗi hay lấy giá trị tuyệt đối
                # print(f"WARNING: Radius âm ({r}) ở dòng {i+1}. Lấy giá trị tuyệt đối.", file=sys.stderr)
                # r = abs(r)
                # Hoặc coi là lỗi:
                print(f"ERROR: Radius không thể âm ({r}) ở dòng {i+1}.", file=sys.stderr)
                error_response = error_response_template.copy()
                error_response["error"] = f"Dữ liệu không hợp lệ: Radius không thể âm (dòng {i+1})."
                return json.dumps(error_response, separators=(',', ':'))

        except KeyError as ke:
            print(f"ERROR: Thiếu key {ke} trong một mục của YBC (dòng {i+1})", file=sys.stderr)
            error_response = error_response_template.copy()
            error_response["error"] = f"Dữ liệu không hợp lệ: Thiếu key {str(ke)} (dòng {i+1})."
            return json.dumps(error_response, separators=(',', ':'))
        except ValueError as ve:
            print(f"ERROR: Giá trị không phải là số trong một mục của YBC (dòng {i+1}): {ve}", file=sys.stderr)
            error_response = error_response_template.copy()
            error_response["error"] = f"Dữ liệu không hợp lệ: Giá trị không phải số (dòng {i+1})."
            return json.dumps(error_response, separators=(',', ':'))

        print(f"\nProcessing Step {i+1}: Y={y}, B={b_deg}, C={c_deg}, R={r}", file=sys.stderr)
        print(f"  State before: P={current_point.tolist()}, D={current_direction.tolist()}, U={current_up_vector.tolist()}", file=sys.stderr)

        # 1. Feed Y_i (Đẩy ống)
        if abs(y) > 1e-9: # Chỉ thực hiện nếu y khác 0
            current_point = current_point + y * current_direction
            centerline_points_forward.append(current_point.copy())
            print(f"  After Feed Y{i+1}: P={current_point.tolist()}", file=sys.stderr)
            end_idx_for_segment = len(centerline_points_forward) - 1
            segment_details.append({'type': 'Y', 'value': y, 'start_idx': start_idx_for_segment, 'end_idx': end_idx_for_segment})
            start_idx_for_segment = end_idx_for_segment
        else:
            print(f"  Feed Y{i+1} skipped (Y is zero or too small)", file=sys.stderr)

        # Lưu trạng thái trước khi uốn và xoay
        direction_before_bend_or_rotate = current_direction.copy()
        up_vector_for_bend_plane = current_up_vector.copy() # U này xác định mặt phẳng cho thao tác Bend B

        # 2. Bend B_i (Uốn ống)
        if abs(b_deg) > 1e-6: # Chỉ uốn nếu góc B khác 0
            if r < 1e-9: # Bán kính phải đủ lớn để uốn
                print(f"  WARNING: Bend B{i+1} skipped. Radius R ({r}) is zero or too small for bending.", file=sys.stderr)
            else:
                b_rad = math.radians(b_deg)
                print(f"  Bending B{i+1}={b_deg} deg, R={r}. Using Up vector U_bend_plane={up_vector_for_bend_plane.tolist()} to define bend plane.", file=sys.stderr)

                # Vector vuông góc với hướng tiến (D) và vector Up (U_bend_plane), nằm trong mặt phẳng uốn.
                # Vector này chỉ hướng từ điểm uốn đến tâm của cung tròn uốn.
                # Quy ước: Quay từ D sang U_bend_plane theo chiều dương (vặn nút chai) sẽ ra perp_vector.
                # Dấu của b_deg sẽ quyết định chiều quay quanh trục bend_axis.
                perp_vector_to_center = np.cross(up_vector_for_bend_plane, direction_before_bend_or_rotate)
                norm_perp_vector = np.linalg.norm(perp_vector_to_center)

                if norm_perp_vector < 1e-9:
                    print(f"  ERROR: Cannot perform bend B{i+1}. Direction vector and Up vector for bend plane are parallel. D={direction_before_bend_or_rotate.tolist()}, U_bend_plane={up_vector_for_bend_plane.tolist()}", file=sys.stderr)
                    error_response = error_response_template.copy()
                    error_response["error"] = f"Lỗi tính toán: Không thể uốn ở bước {i+1} (Direction và Up song song)."
                    return json.dumps(error_response, separators=(',', ':'))

                perp_vector_to_center_normalized = perp_vector_to_center / norm_perp_vector
                bend_center = current_point + r * perp_vector_to_center_normalized # Tâm của cung tròn uốn

                # Trục uốn (bend_axis) là vector Up xác định mặt phẳng uốn.
                # Quay quanh trục này.
                bend_axis = up_vector_for_bend_plane

                print(f"    Bend Axis (U_bend_plane): {bend_axis.tolist()}", file=sys.stderr)
                print(f"    Direction to Bend Center (perp_vec_norm): {perp_vector_to_center_normalized.tolist()}", file=sys.stderr)
                print(f"    Bend Center: {bend_center.tolist()}", file=sys.stderr)

                start_vector_from_center_to_point = current_point - bend_center # Vector từ tâm đến điểm bắt đầu uốn trên cung

                for j in range(1, num_arc_points + 1):
                    angle_step_rad = b_rad * (j / float(num_arc_points)) # Góc quay từng bước
                    # Quay vector từ tâm đến điểm hiện tại quanh trục uốn
                    arc_point_vector_from_center = rotate_vector(start_vector_from_center_to_point, bend_axis, angle_step_rad)
                    centerline_points_forward.append((bend_center + arc_point_vector_from_center).copy())

                # Cập nhật điểm và hướng hiện tại sau khi uốn
                current_point = centerline_points_forward[-1]
                current_direction = rotate_vector(direction_before_bend_or_rotate, bend_axis, b_rad)
                # Chuẩn hóa lại current_direction để tránh tích lũy sai số
                norm_current_d = np.linalg.norm(current_direction)
                if norm_current_d > 1e-9:
                    current_direction = current_direction / norm_current_d
                else: # Hiếm khi xảy ra nếu logic đúng
                    print(f"  ERROR: Zero direction vector after bend B{i+1}. This should not happen.", file=sys.stderr)
                    error_response = error_response_template.copy()
                    error_response["error"] = f"Lỗi tính toán: Hướng vector bằng không sau khi uốn ở bước {i+1}."
                    return json.dumps(error_response, separators=(',', ':'))


                print(f"  After Bend B{i+1}: P={current_point.tolist()}, New D={current_direction.tolist()}", file=sys.stderr)
                end_idx_for_segment = len(centerline_points_forward) - 1
                segment_details.append({'type': 'B', 'angle': b_deg, 'radius': r, 'start_idx': start_idx_for_segment, 'end_idx': end_idx_for_segment})
                start_idx_for_segment = end_idx_for_segment
        else:
            print(f"  Bend B{i+1} skipped (B angle is zero or too small).", file=sys.stderr)


        # 3. Rotate C_i (Xoay mặt phẳng uốn cho bước tiếp theo)
        # Thao tác này sẽ cập nhật current_up_vector để sử dụng cho bước uốn (B) tiếp theo.
        # Trục xoay cho C là current_direction (hướng của ống SAU khi uốn B ở bước hiện tại, hoặc trước đó nếu không có uốn B).
        axis_for_C_rotation = current_direction

        if abs(c_deg) > 1e-6: # Chỉ xoay nếu góc C khác 0
            c_rad = math.radians(c_deg)
            # Vector Up cần xoay là up_vector_for_bend_plane (U đã dùng để xác định mặt phẳng uốn B_i)
            # hoặc là current_up_vector từ bước trước nếu B_i không xảy ra.
            # Về cơ bản, đó là current_up_vector *trước* khi nó được cập nhật bởi C_i này.
            up_vector_to_be_rotated = up_vector_for_bend_plane # Hoặc current_up_vector nếu B không xảy ra, nhưng logic này đã bao hàm

            print(f"  Rotate C{i+1}={c_deg} deg: Rotating Up vector ({up_vector_to_be_rotated.tolist()}) around current Direction D ({axis_for_C_rotation.tolist()})", file=sys.stderr)

            new_up_vector = rotate_vector(up_vector_to_be_rotated, axis_for_C_rotation, c_rad)

            # Ổn định new_up_vector: đảm bảo nó vuông góc với current_direction (axis_for_C_rotation)
            # bằng cách trừ đi thành phần chiếu lên current_direction (phép chiếu Gram-Schmidt)
            projection_on_D = np.dot(new_up_vector, axis_for_C_rotation) * axis_for_C_rotation
            orthogonal_up_vector = new_up_vector - projection_on_D
            norm_orthogonal_up_vector = np.linalg.norm(orthogonal_up_vector)

            if norm_orthogonal_up_vector >= 1e-9:
                current_up_vector = orthogonal_up_vector / norm_orthogonal_up_vector # Chuẩn hóa
                print(f"    New Up vector for next step (U_next): {current_up_vector.tolist()}", file=sys.stderr)
            else:
                # Trường hợp này xảy ra nếu new_up_vector song song với current_direction sau khi xoay,
                # điều này có nghĩa là up_vector_to_be_rotated ban đầu đã song song với current_direction,
                # hoặc một lỗi tính toán nghiêm trọng.
                # Điều này không nên xảy ra nếu D và U luôn vuông góc.
                print(f"    WARNING: Up vector became parallel to Direction after C{i+1} rotation or zero norm. U_input={up_vector_to_be_rotated.tolist()}, D_axis={axis_for_C_rotation.tolist()}, Rotated_U_raw={new_up_vector.tolist()}", file=sys.stderr)
                # Cố gắng phục hồi bằng cách chọn một vector vuông góc mặc định nếu có thể,
                # ví dụ, nếu D không phải là (0,0,1), thì U_new có thể là (0,0,1) x D.
                # Tuy nhiên, để đơn giản, ở đây chỉ cảnh báo và có thể giữ U cũ.
                # Hoặc, nghiêm trọng hơn, đây có thể là một lỗi logic cần được sửa.
                # Giữ lại current_up_vector từ trước khi xoay C có thể không đúng.
                # current_up_vector = up_vector_to_be_rotated # Tạm thời giữ U cũ để tránh lỗi, nhưng cần xem xét lại
                print(f"    Keeping previous Up vector due to issue: {current_up_vector.tolist()}", file=sys.stderr)


        else:
            print(f"  Rotate C{i+1} skipped (C angle is zero or too small). Up vector remains: {current_up_vector.tolist()}", file=sys.stderr)
            # Nếu C=0, current_up_vector không thay đổi so với up_vector_for_bend_plane
            # current_up_vector = up_vector_for_bend_plane # Đã đúng

        print(f"  End of Step {i+1}: P={current_point.tolist()}, D={current_direction.tolist()}, Final U for this step (U_next)={current_up_vector.tolist()}", file=sys.stderr)


    # 4. Chuẩn bị dữ liệu Output JSON
    print("\n--- Tính toán Forward hoàn tất ---", file=sys.stderr)
    P_final_forward = current_point.copy()
    D_final_forward = current_direction.copy()
    U_final = current_up_vector.copy() # Vector Up cuối cùng

    print(f"Final Point: {P_final_forward.tolist()}", file=sys.stderr)
    print(f"Final Direction: {D_final_forward.tolist()}", file=sys.stderr)
    print(f"Final Up Vector: {U_final.tolist()}", file=sys.stderr)

    output_data = {
        "centerline_points": [p.tolist() for p in centerline_points_forward],
        "segment_info": segment_details,
        "final_point": P_final_forward.tolist(),
        "final_direction": D_final_forward.tolist(),
        "final_up_vector": U_final.tolist(), # Thêm thông tin vector Up cuối cùng
        "diameter": tube_diameter
    }

    return json.dumps(output_data, separators=(',', ':'))

# Bạn có thể thêm một khối if __name__ == "__main__": ở đây để test nhanh file này
# ví dụ:
if __name__ == "__main__":
    print("Chạy thử nghiệm YBC3D_web.py độc lập...")

    # Dữ liệu mẫu
    sample_data_1 = {
        "Diameter": 25.4,
        "YBC": [
            {"Y": 100, "B": 90, "C": 0, "Radius": 50},
            {"Y": 80, "B": 45, "C": 90, "Radius": 60},
            {"Y": 120, "B": 0, "C": 0, "Radius": 0} # Radius 0 ở đây không có ý nghĩa cho uốn, B=0 nên sẽ bỏ qua
        ]
    }

    sample_data_error_type = {
        "Diameter": "abc", # Lỗi kiểu dữ liệu
        "YBC": [
            {"Y": 100, "B": 90, "C": 0, "Radius": 50}
        ]
    }

    sample_data_missing_key = {
        "Diameter": 30,
        "YBC": [
            {"Y": 100, "B": 90, "Radius": 50} # Thiếu 'C'
        ]
    }
    
    sample_data_empty_ybc = {
        "Diameter": 30,
        "YBC": []
    }

    print("\n--- Test với sample_data_1 ---")
    result_json_1 = calculate_centerline_from_data(sample_data_1)
    print("Kết quả JSON 1:\n", json.dumps(json.loads(result_json_1), indent=2)) # In đẹp hơn

    print("\n--- Test với sample_data_error_type (lỗi kiểu dữ liệu Diameter) ---")
    result_json_error_type = calculate_centerline_from_data(sample_data_error_type)
    print("Kết quả JSON (lỗi type):\n", json.dumps(json.loads(result_json_error_type), indent=2))

    print("\n--- Test với sample_data_missing_key (thiếu key 'C') ---")
    result_json_missing_key = calculate_centerline_from_data(sample_data_missing_key)
    print("Kết quả JSON (thiếu key):\n", json.dumps(json.loads(result_json_missing_key), indent=2))

    print("\n--- Test với sample_data_empty_ybc (YBC rỗng) ---")
    result_json_empty_ybc = calculate_centerline_from_data(sample_data_empty_ybc)
    print("Kết quả JSON (YBC rỗng):\n", json.dumps(json.loads(result_json_empty_ybc), indent=2))