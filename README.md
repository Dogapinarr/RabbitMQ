Payment Application
This simple application consists of a web service allowing users to pay their invoices and a backend service to handle payment processes. Flask is used for the web server, RabbitMQ for the backend service, and SQLite for storing user and invoice data.

Requirements
Python 3.x
Flask
pika (for RabbitMQ)
SQLite
Installation
Install the required libraries by running the following command:

pip install flask pika

Run the app.py file to start the application:

python app.py

View the application by navigating to http://localhost:5000 in your browser.

Usage

Pay Bill: Send a payment request by using the POST /v1/website/pay-bill endpoint. The request body should include the subscriber number (subscriber_no) and the month of the invoice (month).

Important Notes

This application is intended as a sample and is not suitable for real-world usage. Considerations such as security, performance, and scalability should be taken into account.
SQLite is suitable for small-scale applications, but a more robust database management system should be considered for large-scale applications.
