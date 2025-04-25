from app import app
import routes  # 👈 Chỉ cần import để route được đăng ký

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
