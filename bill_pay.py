from flask import Flask, request, jsonify
import pika  # RabbitMQ için kullanılan kütüphane
import sqlite3
import json

app = Flask(__name__)

QUEUE_HOST = 'localhost'
QUEUE_PORT = 5672
QUEUE_USERNAME = 'guest'
QUEUE_PASSWORD = 'guest'

PAYMENT_QUEUE_NAME = 'payment_queue'

DATABASE = 'database.db'

def create_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bills (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 subscriber_no TEXT,
                 month TEXT,
                 total INTEGER,
                 details TEXT,
                 paid_status BOOLEAN,
                 FOREIGN KEY(subscriber_no) REFERENCES users(subscriber_no)
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 subscriber_no TEXT UNIQUE,
                 password TEXT
                 )''')

    conn.commit()
    conn.close()

def insert_data(subscriber_no, month, total, details, paid_status):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("SELECT id FROM bills WHERE subscriber_no=? AND month=?", (subscriber_no, month))
    existing_record = c.fetchone()
    
    if existing_record is None:
        c.execute("INSERT INTO bills (subscriber_no, month, total, details, paid_status) VALUES (?, ?, ?, ?, ?)",
                  (subscriber_no, month, total, details, paid_status))
        conn.commit()
        print("Yeni veri eklendi.")
    else:
        print("Veri zaten veritabanında var.")
    
    conn.close()

    insert_data("ayşe", "2024-04", 100, "Some details", False)


def insert_user_data(subscriber_no, password):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("SELECT id FROM users WHERE subscriber_no=?", (subscriber_no,))
    existing_record = c.fetchone()
    
    if existing_record is None:
        c.execute("INSERT INTO users (subscriber_no, password) VALUES (?, ?)",
                  (subscriber_no, password))
        conn.commit()
        print("Yeni kullanıcı eklendi.")
    else:
        print("Kullanıcı zaten veritabanında var.")
    
    conn.close()

insert_user_data("ayşe", "123")



def process_payment_requests():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=QUEUE_HOST, port=QUEUE_PORT, credentials=pika.PlainCredentials(QUEUE_USERNAME, QUEUE_PASSWORD)))
    except pika.exceptions.AMQPConnectionError as e:
        print("Error connecting to RabbitMQ:", e)
        return  # Exit the function if connection cannot be established
    
    channel = connection.channel()
    channel.queue_declare(queue=PAYMENT_QUEUE_NAME)

    def callback(ch, method, properties, body):
        payment_info = json.loads(body)
        user_no = payment_info["user_no"]
        month = payment_info["month"]
        total = payment_info["total"]

        success = perform_payment(user_no, month, total)

        if success:
            update_bill_status(user_no, month)
            print("Payment processed for user_no:", user_no)
        else:
            print("Payment processing failed for user_no:", user_no)

    channel.basic_consume(queue=PAYMENT_QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print("Payment processing started...")
    channel.start_consuming()

def perform_payment(user_no, month, total):
  
    return True  # Geçici olarak her zaman başarılı kabul ediyoruz

def update_bill_status(user_no, month):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE bills SET paid_status = ? WHERE subscriber_no = ? AND month = ?",
              (True, user_no, month))
    conn.commit()
    conn.close()

process_payment_requests()

@app.route('/v1/website/pay-bill', methods=['POST'])
def pay_bill():
    subscriber_no = request.json.get('subscriber_no')
    month = request.json.get('month')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT paid_status FROM bills WHERE subscriber_no=? AND month=?", (subscriber_no, month))
    bill_status = c.fetchone()

    if not bill_status:
        conn.close()
        return jsonify({"error": "Bill not found"}), 404

    if bill_status[0]: 
        conn.close()
        return jsonify({"payment_status": "Error", "message": "Invoice already paid."}), 400

    payment_info = {
        "user_no": subscriber_no,
        "month": month,
        "total": 100  
    }
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=QUEUE_HOST, port=QUEUE_PORT, credentials=pika.PlainCredentials(QUEUE_USERNAME, QUEUE_PASSWORD)))
    channel = connection.channel()
    channel.queue_declare(queue=PAYMENT_QUEUE_NAME)
    channel.basic_publish(exchange='', routing_key=PAYMENT_QUEUE_NAME, body=json.dumps(payment_info))
    connection.close()

    conn.close()

    return jsonify({"payment_status": "In Progress", "message": "Payment request sent for processing."}), 200

if __name__ == '__main__':
    create_db()
    app.run(debug=True)
