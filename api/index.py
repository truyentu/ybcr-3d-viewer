# File: api/index.py

# Đảm bảo các dòng import này không có khoảng trắng/tab ở đầu dòng
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import os

# Các dòng comment cũng không nên có thụt đầu dòng không cần thiết
# Quan trọng: Khi triển khai lên Vercel, các file trong thư mục 'api'
# có thể được coi là đang ở thư mục gốc của môi trường serverless.
# Chúng ta cần đảm bảo YBC3D_web.py được import đúng cách.
try: # Khối try bắt đầu ở đây, các dòng bên trong nó sẽ được thụt vào
    # Thử import trực tiếp nếu Vercel đặt các file cùng cấp khi build
    from YBC3D_web import calculate_centerline_from_data
except ImportError:
    # Nếu không được, thử import từ thư mục hiện tại (thường là 'api')
    # Điều này có thể cần thiết tùy theo cách Vercel build
    try:
        from .YBC3D_web import calculate_centerline_from_data
    except ImportError as e:
        # Sử dụng logging của Python thay vì print trực tiếp trong môi trường serverless
        # logging.critical sẽ được Vercel ghi lại
        logging.critical(f"LỖI NGHIÊM TRỌNG: Không thể import 'calculate_centerline_from_data' từ YBC3D_web.py. Lỗi: {e}")
        logging.critical("Đường dẫn sys.path hiện tại: %s", os.sys.path)
        # Dòng này sẽ giúp bạn kiểm tra Vercel có "thấy" file YBC3D_web.py không
        # Trong môi trường Vercel, thư mục làm việc thường là /var/task
        current_dir_content = "Không thể liệt kê thư mục."
        try:
            current_dir_content = os.listdir('.' if os.path.exists('.') else '/var/task/api') # Thử /var/task/api nếu '.' không hoạt động
            # Hoặc os.listdir(os.path.dirname(__file__)) # Lấy thư mục của file hiện tại
        except Exception as list_dir_e:
            current_dir_content = f"Lỗi khi liệt kê thư mục: {list_dir_e}"

        logging.critical(f"Các file trong thư mục hiện tại (dự kiến là api/): {current_dir_content}")


        def calculate_centerline_from_data(data_dict): # Hàm giả
            return json.dumps({
                "error": "Lỗi cấu hình server: Chức năng tính toán không khả dụng do lỗi import module YBC3D_web.",
                "centerline_points": [], "segment_info": [],
                "final_point": [0,0,0], "final_direction": [1,0,0],
                "final_up_vector": [0,0,1],
                "diameter": data_dict.get("Diameter", 30.0),
                "profile": data_dict.get("profile_in_request", {})
            })

# Khởi tạo ứng dụng Flask
# Dòng này cũng không được thụt đầu dòng
app = Flask(__name__)
CORS(app) # Cho phép CORS cho tất cả các route

# Cấu hình logger của Flask
if not app.debug:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


@app.route('/api/calculate_tube', methods=['POST'])
def handle_calculate_tube():
    # Các dòng bên trong hàm này sẽ được thụt vào một cấp
    app.logger.info(f"Yêu cầu nhận được tại /api/calculate_tube với phương thức {request.method}")
    try:
        input_data = request.get_json()
        if not input_data:
            app.logger.warning("Dữ liệu đầu vào rỗng hoặc không phải JSON.")
            return jsonify({"error": "Dữ liệu đầu vào không hợp lệ."}), 400
        
        app.logger.info(f"Dữ liệu đầu vào đã parse: {input_data}")

        profile_info_from_request = input_data.get('profile')
        ybc_data_from_request = input_data.get('YBC')

        if not profile_info_from_request or not isinstance(profile_info_from_request, dict):
            app.logger.warning("Thiếu hoặc sai định dạng 'profile' trong request.") # Thêm log
            return jsonify({"error": "Thiếu hoặc sai định dạng 'profile'."}), 400
        if not ybc_data_from_request or not isinstance(ybc_data_from_request, list):
            app.logger.warning("Thiếu hoặc sai định dạng 'YBC' trong request.") # Thêm log
            return jsonify({"error": "Thiếu hoặc sai định dạng 'YBC'."}), 400

        data_for_centerline_calc = {'YBC': ybc_data_from_request}
        if profile_info_from_request.get('type') == 'round':
            dimensions = profile_info_from_request.get('dimensions', {})
            if 'diameter' in dimensions:
                data_for_centerline_calc['Diameter'] = dimensions['diameter']
        
        # Kiểm tra hàm tính toán
        # Đảm bảo calculate_centerline_from_data không phải là hàm giả do lỗi import
        if not callable(calculate_centerline_from_data) or \
          (hasattr(calculate_centerline_from_data, '__name__') and calculate_centerline_from_data.__name__ == '<lambda>' and "Lỗi cấu hình server" in calculate_centerline_from_data({}).get("error","")):
            app.logger.error("Hàm 'calculate_centerline_from_data' không khả dụng (có thể do lỗi import YBC3D_web.py).")
            # Cung cấp thêm thông tin debug về import
            module_path_check = "Không xác định"
            try:
                # __file__ là đường dẫn đến file index.py hiện tại
                # os.path.dirname(__file__) là thư mục chứa index.py (tức là 'api')
                module_path_check = os.path.abspath(os.path.join(os.path.dirname(__file__), "YBC3D_web.py"))
                app.logger.error(f"Kiểm tra sự tồn tại của YBC3D_web.py tại: {module_path_check} - Tồn tại: {os.path.exists(module_path_check)}")
            except Exception as path_e:
                 app.logger.error(f"Lỗi khi kiểm tra đường dẫn YBC3D_web.py: {path_e}")
            
            return jsonify({"error": "Lỗi server: Chức năng tính toán không khả dụng (lỗi import nội bộ)."}), 500


        result_json_string = calculate_centerline_from_data(data_for_centerline_calc)
        result_data_from_calc = json.loads(result_json_string)
        
        # Kiểm tra lỗi trả về từ hàm calculate_centerline_from_data
        if "error" in result_data_from_calc and result_data_from_calc["error"]:
             app.logger.warning(f"Lỗi từ hàm tính toán YBCR: {result_data_from_calc['error']}")
             return jsonify(result_data_from_calc), 400 # Trả về lỗi do người dùng cung cấp dữ liệu sai

        final_response_data = result_data_from_calc.copy()
        final_response_data['profile'] = profile_info_from_request # Thêm thông tin biên dạng
        
        app.logger.info(f"Phản hồi cuối cùng: {final_response_data}")
        return jsonify(final_response_data), 200

    except json.JSONDecodeError as jde:
        app.logger.error(f"Lỗi parse JSON từ request: {jde}", exc_info=True)
        return jsonify({"error": f"JSON không hợp lệ trong request: {str(jde)}"}), 400
    except Exception as e: # Bắt các lỗi chung khác
        app.logger.error(f"Lỗi server không xác định trong handle_calculate_tube: {e}", exc_info=True)
        return jsonify({"error": "Lỗi server không mong muốn."}), 500

# KHÔNG CẦN app.run() khi triển khai lên Vercel
