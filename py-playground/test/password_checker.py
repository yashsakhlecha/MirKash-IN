import re

def check_password_strength(password):
    # Criteria for a strong password
    length_criteria = len(password) >= 8  # At least 8 characters
    uppercase_criteria = bool(re.search(r'[A-Z]', password))  # At least one uppercase letter
    lowercase_criteria = bool(re.search(r'[a-z]', password))  # At least one lowercase letter
    number_criteria = bool(re.search(r'[0-9]', password))  # At least one digit
    special_char_criteria = bool(re.search(r'[\W_]', password))  # At least one special character

    # Check if all criteria are met
    if length_criteria and uppercase_criteria and lowercase_criteria and number_criteria and special_char_criteria:
        return "Strong password!"
    else:
        # Add specific conditions to help the user
        strength_message = []
        if not length_criteria:
            strength_message.append("- At least 8 characters")
        if not uppercase_criteria:
            strength_message.append("- At least one uppercase letter")
        if not lowercase_criteria:
            strength_message.append("- At least one lowercase letter")
        if not number_criteria:
            strength_message.append("- At least one number")
        if not special_char_criteria:
            strength_message.append("- At least one special character (e.g., !, @, #, $, etc.)")
        
        return "Weak password. It should have:\n" + "\n".join(strength_message)

# Example usage
password = input("Enter your password to check its strength: ")
result = check_password_strength(password)
print(result)
