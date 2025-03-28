from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import get_db_connection
from zk import ZK
import time

app = Flask(__name__)

# ZKTeco Connection
zk = ZK('192.168.1.201', port=4370)

@app.route('/')
def index():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    db.close()
    return render_template('index.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        user_id = request.form['user_id']
        name = request.form['name']
        enroll_type = request.form['enroll_type']

        try:
            conn = zk.connect()
            conn.disable_device()  # Disable device to avoid conflicts

            # ✅ Step 1: Diiwaangeli user ID & Name qalabka
            conn.set_user(uid=int(user_id), name=name, privilege=0, password="")

            # ✅ Step 2: Wuxuu bilaabayaa Face/Fingerprint scan isla markiiba
            if enroll_type == "face":
                print("📸 Please scan your face on the device NOW!")
                conn.test_voice()  # Play voice to instruct user
            elif enroll_type == "finger":
                print("🖐 Please scan your fingerprint on the device NOW!")
                conn.test_voice()

            conn.enable_device()
            conn.disconnect()

            # ✅ Step 3: Sug inta user uu dhammeeyo Face/Finger scan
            print("⌛ Waiting for user to complete enrollment...")
            time.sleep(15)  # Wuxuu sugayaa 15s user in uu dhammeeyo scan

            # ✅ Step 4: Hubi haddii user uu dhameystiray Face/Finger
            conn = zk.connect()
            users = conn.get_users()
            enrolled = any(str(user.user_id) == user_id for user in users)

            if enrolled:
                # ✅ Haddii user uu dhammeeyo, keydi MySQL
                db = get_db_connection()
                cursor = db.cursor()
                cursor.execute("INSERT INTO user (user_id, name) VALUES (%s, %s)", (user_id, name))
                db.commit()
                db.close()
                print("✅ User successfully registered in MySQL & Device")
            else:
                print("❌ User enrollment failed. Please try again.")

            conn.disconnect()

        except Exception as e:
            return f"Error enrolling user: {e}"

        return redirect(url_for('index'))

    return render_template('add_user.html')

if __name__ == '__main__':
    app.run(debug=True)
