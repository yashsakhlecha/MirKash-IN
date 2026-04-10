from flask import Flask, render_template_string, request

app = Flask(__name__)

HTML = '''
<!doctype html>
<title>Celsius to Fahrenheit Converter</title>
<h2>Celsius to Fahrenheit Converter</h2>
<form method="post">
  <label for="celsius">Celsius:</label>
  <input type="number" step="any" name="celsius" id="celsius" required>
  <input type="submit" value="Convert">
</form>
{% if result is not none %}
  <h3>{{ celsius }}°C is equal to {{ result }}°F</h3>
{% endif %}
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    celsius = ''
    if request.method == 'POST':
        try:
            celsius = float(request.form['celsius'])
            result = round((celsius * 9/5) + 32, 2)
        except ValueError:
            result = 'Invalid input'
    return render_template_string(HTML, result=result, celsius=celsius)

if __name__ == '__main__':
    app.run(debug=True) 