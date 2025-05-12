    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import json
    import logging
    import os # Thêm os để có thể làm việc với đường dẫn file một cách linh hoạt

    # Quan trọng: Khi triển khai lên Vercel, các file trong thư mục 'api'
    # có thể được coi là đang ở thư mục gốc của môi trường serverless.
    # Chúng ta cần đảm bảo YBC3D_web.py được import đúng cách.
    try:
        # Thử import trực tiếp nếu Vercel đặt các file cùng cấp khi build
        from YBC3D_web import calculate_centerline_from_data
    except ImportError:
        # Nếu không được, thử import từ thư mục hiện tại (thường là 'api')
        # Điều này có thể cần thiết tùy theo cách Vercel build
        try:
            from .YBC3D_web import calculate_centerline_from_data
        except ImportError as e:
            logging.critical(f"LỖI NGHIÊM TRỌNG: Không thể import 'calculate_centerline_from_data' từ YBC3D_web.py. Lỗi: {e}")
            logging.critical("Đường dẫn sys.path hiện tại: %s", os.sys.path)
            logging.critical("Các file trong thư mục hiện tại (api/): %s", os.listdir('.' if os.path.exists('.') else '/var/task'))


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
    # Vercel sẽ tự động tìm biến 'app' này
    app = Flask(__name__)
    CORS(app) # Cho phép CORS cho tất cả các route

    # Không cần logging.basicConfig vì Vercel có hệ thống logging riêng,
    # nhưng bạn có thể giữ lại nếu muốn log chi tiết hơn khi debug local.
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    # Thay vào đó, sử dụng app.logger của Flask
    if not app.debug: # Chỉ cấu hình logger nếu không ở chế độ debug (Vercel thường không chạy ở debug mode)
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)


    @app.route('/api/calculate_tube', methods=['POST'])
    def handle_calculate_tube(): # Đổi tên hàm để tránh trùng với tên module/biến
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
                return jsonify({"error": "Thiếu hoặc sai định dạng 'profile'."}), 400
            if not ybc_data_from_request or not isinstance(ybc_data_from_request, list):
                return jsonify({"error": "Thiếu hoặc sai định dạng 'YBC'."}), 400

            data_for_centerline_calc = {'YBC': ybc_data_from_request}
            if profile_info_from_request.get('type') == 'round':
                dimensions = profile_info_from_request.get('dimensions', {})
                if 'diameter' in dimensions:
                    data_for_centerline_calc['Diameter'] = dimensions['diameter']
            
            # Kiểm tra hàm tính toán (quan trọng cho debug trên Vercel)
            if not callable(calculate_centerline_from_data) or \
              (hasattr(calculate_centerline_from_data, '__name__') and calculate_centerline_from_data.__name__ == '<lambda>'):
                app.logger.error("Hàm 'calculate_centerline_from_data' không khả dụng hoặc là hàm giả.")
                # Cung cấp thêm thông tin debug về import
                module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "YBC3D_web.py"))
                app.logger.error(f"Kiểm tra sự tồn tại của YBC3D_web.py tại: {module_path} - Tồn tại: {os.path.exists(module_path)}")
                return jsonify({"error": "Lỗi server: Chức năng tính toán không khả dụng (lỗi import nội bộ)."}), 500


            result_json_string = calculate_centerline_from_data(data_for_centerline_calc)
            result_data_from_calc = json.loads(result_json_string)
            
            if "error" in result_data_from_calc and result_data_from_calc["error"]:
                 app.logger.warning(f"Lỗi từ hàm tính toán YBCR: {result_data_from_calc['error']}")
                 return jsonify(result_data_from_calc), 400

            final_response_data = result_data_from_calc.copy()
            final_response_data['profile'] = profile_info_from_request
            
            app.logger.info(f"Phản hồi cuối cùng: {final_response_data}")
            return jsonify(final_response_data), 200

        except json.JSONDecodeError as jde:
            app.logger.error(f"Lỗi parse JSON: {jde}", exc_info=True)
            return jsonify({"error": f"JSON không hợp lệ: {str(jde)}"}), 400
        except Exception as e:
            app.logger.error(f"Lỗi server không xác định: {e}", exc_info=True)
            return jsonify({"error": "Lỗi server không mong muốn."}), 500

    # KHÔNG CẦN app.run() khi triển khai lên Vercel
    # if __name__ == '__main__':
    #     app.run(host='0.0.0.0', port=5000, debug=True)
    