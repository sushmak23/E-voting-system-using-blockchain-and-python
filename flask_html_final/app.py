import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
from datetime import datetime, date, timedelta
from blockchain import Blockchain  
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your email provider's SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'votingapp.viit@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'nvzmxclelqrzjdyn'  # Replace with your email's app password
app.config['MAIL_DEFAULT_SENDER'] = 'votingapp.viit@gmail.com'

mail = Mail(app)


# Configure session timeout
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
blockchain = Blockchain()

# File paths
VOTER_CSV = 'data/voters.csv'
CSV_FILE = 'data/votes.csv'

# Ensure data directories exist
os.makedirs('data', exist_ok=True)

# Ensure voters.csv exists
if not os.path.exists(VOTER_CSV):
    pd.DataFrame(columns=['name', 'dob', 'age', 'address', 'gender', 'voter_id', 'password']).to_csv(VOTER_CSV, index=False)

# Ensure votes.csv exists
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=['voter_id', 'party', 'timestamp']).to_csv(CSV_FILE, index=False)


def calculate_age(dob):
    """
    Calculate age from the date of birth (dob).
    :param dob: Date of birth in 'YYYY-MM-DD' format.
    :return: Age as an integer.
    """
    try:
        birth_date = datetime.strptime(dob, '%Y-%m-%d').date()
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.")
        return None
    

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        email = request.form['email']
        dob = request.form['dob']
        address = request.form['address']
        gender = request.form['gender']
        voter_id = request.form['voter_id']
        password = request.form['password']
        
        # Calculate age based on date of birth
        age = calculate_age(dob)

        # Check for duplicate voter_id and email
        try:
            voter_df = pd.read_csv(VOTER_CSV)
            if voter_id in voter_df['voter_id'].astype(str).values:
                flash("Voter ID already exists. Please use a unique ID.")
                return redirect(url_for('signup'))
            if email in voter_df['email'].astype(str).values:
                flash("Email already registered. Please use a unique email.")
                return redirect(url_for('signup'))
        except FileNotFoundError:
            # If the CSV doesn't exist, proceed (this means no existing data yet)
            voter_df = pd.DataFrame()
        
        # Validate age
        if age < 18:
            flash("Age less than 18, cannot register.")
            return redirect(url_for('signup'))
        elif age > 120:
            flash("Please write correct age.")
            return redirect(url_for('signup'))
        
        # Validate name (no numbers allowed)
        if not name.isalpha():
            flash("Invalid name. Name should contain only alphabetic characters (A-Z, a-z).")
            return redirect(url_for('signup'))
        
        # Validate email format
        if '@' not in email or '.' not in email.split('@')[-1]:
            flash("Invalid email address.")
            return redirect(url_for('signup'))

        # Validate id (no characters allowed)
        if not voter_id.isnumeric():
            flash("Invalid Voter id. Id should contain only numbers.")
            return redirect(url_for('signup'))
        
        # Validate password length
        if len(password) < 6:
            flash("Please write a longer password. Minimum 6 characters required.")
            return redirect(url_for('signup'))
        
        # If all validations pass, create new voter entry
        new_voter = pd.DataFrame([{
            'name': name,
            'email': email,
            'dob': dob,
            'age': age,
            'address': address,
            'gender': gender,
            'voter_id': voter_id,
            'password': password
        }])

        try:
            voter_df = pd.read_csv(VOTER_CSV)
            voter_df = pd.concat([voter_df, new_voter], ignore_index=True)
            voter_df.to_csv(VOTER_CSV, index=False)
        except Exception as e:
            flash("Error saving data. Please try again.")
            return redirect(url_for('signup'))

        flash("Signup successful!")
        return redirect('/')
    
    return render_template('signup.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        voter_id = request.form.get('voter_id')
        password = request.form.get('password')

        voters = pd.read_csv(VOTER_CSV)
        voters['voter_id'] = voters['voter_id'].astype(str)
        voters['password'] = voters['password'].astype(str)

        voter = voters[(voters['voter_id'] == voter_id) & (voters['password'] == password)]

        if not voter.empty:
            # flash("Login successful!")
            return redirect(url_for('voting'))
        else:
            flash("Invalid Voter ID or Password")
            return redirect(url_for('signin'))
    return render_template('signin.html')


@app.route('/voting', methods=['GET', 'POST'])
def voting():
    if request.method == 'POST':
        voter_id = request.form.get('voter_id')
        party = request.form.get('party')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        voters = pd.read_csv(VOTER_CSV)
        votes = pd.read_csv(CSV_FILE)

        # Validate voter ID
        if not voters['voter_id'].astype(str).str.contains(voter_id).any():
            flash("Invalid Voter ID. Please try again.")
            return redirect(url_for('voting'))

        # Check if the voter has already voted
        if votes['voter_id'].astype(str).str.contains(voter_id).any():
            flash("You have already voted.")
            return redirect(url_for('home'))

        # Get voter email for confirmation
        voter_email = voters.loc[voters['voter_id'] == int(voter_id), 'email'].values[0]
        print(voter_email)

        # Record the vote
        vote_data = {'voter_id': voter_id, 'party': party, 'timestamp': timestamp}
        pd.DataFrame([vote_data]).to_csv(CSV_FILE, mode='a', header=False, index=False)

        # Send confirmation email
        try:
            msg = Message(
                subject="Vote Confirmation",
                recipients=[voter_email],
                body=f"Dear Voter,\n\nYour vote for '{party}' has been successfully recorded on {timestamp}.\n\nThank you for participating in the election process.\n\nBest Regards,\nElection Commission"
            )
            mail.send(msg)
            flash("Vote submitted successfully! A confirmation email has been sent.")
        except Exception as e:
            flash("Vote submitted successfully! However, we couldn't send a confirmation email.")

        return redirect(url_for('home'))
    return render_template('voting.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_id = request.form['username']
        admin_password = request.form['password']

        if admin_id == "admin" and admin_password == "admin123":
            session['admin_logged_in'] = True
            session.permanent = True
            # flash("Admin login successful!")
            return redirect(url_for('admin'))
        else:
            flash("Invalid Admin Credentials")
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')


@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        flash("Please log in to access the admin dashboard.")
        return redirect(url_for('admin_login'))

    try:
        votes_df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        votes_df = pd.DataFrame(columns=['voter_id', 'party', 'timestamp'])

    voting_history = votes_df.to_dict(orient='records')
    results = votes_df['party'].value_counts().reset_index()
    results.columns = ['party', 'votes']
    results = results.to_dict(orient='records')

    return render_template('admin.html', voting_history=voting_history, results=results)


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Admin logged out successfully.")
    return redirect(url_for('admin_login'))
@app.route('/mine_block', methods=['POST'])
def mine_block():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Create a new block and reset pending transactions
    block = blockchain.create_block(proof)
    flash("A new block has been mined successfully!")

    return redirect(url_for('admin'))

@app.route('/view_chain')
def view_chain():
    chain = blockchain.chain
    return render_template('view_chain.html', chain=chain)

if __name__ == '__main__':
    app.run(debug=True)

