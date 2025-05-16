import re

def pre_parse(input_str):
    balance = 0
    for char in input_str:
        if char == '(':
            balance += 1
        elif char == ')':
            balance -= 1
        if balance < 0:
            raise ValueError('Not matching parenthesis')
    if balance != 0:
        raise ValueError('Not matching parenthesis')


def get_next(text, start_index):
    if not text:
        raise Exception('End of string (empty input)')
    if start_index >= len(text):
        raise IndexError('End of string (start_index out of bounds)')

    NUM_CHARS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.'}
    WHITESPACE_PARENS = {' ', '\t', '\n', '\r', '(', ')'} # Characters that delimit tokens

    current_index = start_index
    first_char = text[current_index]

    # 1. Try parsing a number (including leading '-')
    # Check for unary minus: at start OR after an operator/opening paren
    is_unary_minus = (first_char == '-' and
                      (start_index == 0 or text[start_index-1] in '+-*/%^('))

    if first_char in NUM_CHARS or is_unary_minus:
        temp_idx = start_index
        num_str = ""

        if is_unary_minus:
            # Check if something follows the minus sign
            if start_index + 1 >= len(text) or text[start_index+1] not in NUM_CHARS:
                 # It's just '-', treat as operator below
                 pass # Fall through to operator parsing
            else:
                num_str = "-"
                temp_idx += 1 # Consume the '-'
        elif first_char == '.': # Allow leading dot e.g. .5
             pass # Let the loop handle it
        elif first_char not in NUM_CHARS: # Should only be '-' case already handled
             pass # Fall through


        # Start parsing the number part
        has_dot = False
        number_parsed = False # Flag to check if we actually parsed digits
        while temp_idx < len(text):
            char = text[temp_idx]
            if char in NUM_CHARS:
                if char == '.':
                    if has_dot: raise ValueError(f"Invalid float format: multiple '.' found starting near index {start_index}")
                    has_dot = True
                num_str += char
                number_parsed = True # Parsed at least one digit or dot
                temp_idx += 1
            else:
                break # Stop at non-numeric

        # Ensure a valid number was formed (more than just '-' if present)
        if number_parsed and num_str != '-':
             try:
                 # Ensure it's not just "."
                 if num_str == ".":
                      raise ValueError("Invalid number format: standalone '.'")
                 # Ensure not just "-."
                 if num_str == "-.":
                      raise ValueError("Invalid number format: standalone '-.'")
                 return (float(num_str) if has_dot else int(num_str)), temp_idx
             except ValueError as e: # Catch conversion errors or specific format errors
                 # Raise a more specific format error if possible
                 if "multiple '.'" in str(e) or "standalone" in str(e):
                      raise e
                 else:
                      raise ValueError(f"Invalid number format found: '{num_str}' starting near index {start_index}") from e

    # 2. If not a number, parse the longest possible operator/identifier token
    token_str = ""
    temp_index = start_index
    while temp_index < len(text):
        char = text[temp_index]
        # Define characters that BREAK a token sequence: digit, whitespace, or parenthesis
        if char.isdigit() or char in WHITESPACE_PARENS:
            break
        token_str += char
        temp_index += 1

    # Ensure *something* was parsed if we didn't parse a number
    if not token_str:
        raise Exception(f"Failed to parse token at index {start_index}. Unexpected character or sequence.")

    return token_str, temp_index


def struct(lst):
    ALL_KNOWN_OPS = {'^', 'pow', '*', 'mul', '/', 'div', '%', 'mod', '+', 'add', '-', 'sub'}
    operator_levels = [{' ^', 'pow'}, {'*', 'mul', '/', 'div', '%', 'mod'}, {'+', 'add', '-', 'sub'}]
    lst_repr = repr(lst)

    if not isinstance(lst, list): raise ValueError(f'Input to struct must be a list, got "{lst_repr}"')
    if not lst: raise ValueError(f'Failed to structure empty list: "{lst_repr}"')
    if len(lst) == 1: return lst[0]

    current_lst = list(lst)
    for ops_in_level in operator_levels:
        temp_lst = []
        i = 0
        while i < len(current_lst):
            token = current_lst[i]
            if i > 0 and i < len(current_lst) - 1 and isinstance(token, str) and token in ops_in_level:
                left_operand = temp_lst.pop()
                right_operand = current_lst[i + 1]
                new_element = [token, left_operand, right_operand]
                temp_lst.append(new_element)
                i += 2
            else:
                temp_lst.append(token)
                i += 1
        current_lst = temp_lst

    # Process remaining tokens (potentially unknown operators/typos) left-to-right
    temp_lst = []
    i = 0
    while i < len(current_lst):
        token = current_lst[i]
        # If it's a string token (could be unknown op or leftover known op if structure is odd)
        # and it's surrounded by operands
        if i > 0 and i < len(current_lst) - 1 and isinstance(token, str):
             left_operand = temp_lst.pop()
             right_operand = current_lst[i+1]
             new_element = [token, left_operand, right_operand]
             temp_lst.append(new_element)
             i += 2
        else:
             temp_lst.append(token)
             i += 1
    current_lst = temp_lst

    if len(current_lst) == 1: return current_lst[0]
    if len(current_lst) == 2: return current_lst
    else: raise ValueError(f'Failed to structure. Unexpected elements remain: "{repr(current_lst)}" from "{lst_repr}"')


def find_matching_paren(text, start_index):
    if text[start_index] != '(': raise ValueError("Starting index is not an opening parenthesis")
    level = 1
    current_index = start_index + 1
    while current_index < len(text):
        char = text[current_index]
        if char == '(': level += 1
        elif char == ')':
            level -= 1
            if level == 0: return current_index
        current_index += 1
    raise ValueError(f"Mismatched parenthesis: No closing parenthesis found for '(' at index {start_index}")


def parse(input_str):
    pre_parse(input_str)
    # Don't remove spaces here, let get_next handle delimiters
    processed_str = input_str # Use original string
    if not processed_str.strip(): raise ValueError("Cannot parse empty or whitespace-only string")

    tokens = []
    i = 0
    while i < len(processed_str):
        # Skip leading whitespace before trying to get the next token
        while i < len(processed_str) and processed_str[i].isspace():
             i += 1
        if i >= len(processed_str): # Reached end after skipping whitespace
             break

        char = processed_str[i]

        if char == '(':
            # Parenthesis handling needs careful index management with spaces
            end_paren_index = find_matching_paren(processed_str, i)
            sub_expression = processed_str[i + 1 : end_paren_index]
            # Recursively parse the sub-expression (which might contain spaces)
            parsed_sub = parse(sub_expression)
            tokens.append(parsed_sub)
            i = end_paren_index + 1
        elif char == ')':
             raise ValueError(f"Internal Error: Unexpected closing parenthesis during parse in '{input_str}' at index {i}")
        else:
            try:
                # Pass the current index 'i' which is start of non-whitespace char
                token, next_i = get_next(processed_str, i)
                tokens.append(token)
                i = next_i # Update index based on what get_next consumed
            except (ValueError, IndexError, Exception) as e:
                 # Improve error context if possible
                 context_start = max(0, i - 10)
                 context_end = min(len(processed_str), i + 10)
                 context = processed_str[context_start:context_end]
                 # Raise preserving original type but adding context
                 raise type(e)(f"Parsing error near index {i} (context: '...{context}...'): {e}") from e

    try:
        if not tokens: raise ValueError("No tokens generated from input string.")
        return struct(tokens)
    except ValueError as e:
         # Add context for structuring errors too
         raise ValueError(f"Structuring error for tokens {repr(tokens)} from '{input_str}': {e}") from e


def eval(lst):
    if isinstance(lst, (int, float)): return lst

    if not isinstance(lst, list) or not lst:
        raise TypeError(f'Internal evaluation error: Invalid/empty list structure "{repr(lst)}"')

    evaluated_elements = [eval(e) if isinstance(e, list) else e for e in lst]

    if len(evaluated_elements) == 1 and isinstance(evaluated_elements[0], (int, float)):
        return evaluated_elements[0]
    if len(evaluated_elements) == 2 and evaluated_elements[0] == '-':
        return -evaluated_elements[1]
    if len(evaluated_elements) != 3:
        raise TypeError(f'Internal evaluation error: Expected 3 elements [op, a, b], got "{repr(evaluated_elements)}"')

    operator, a, b = evaluated_elements[0], evaluated_elements[1], evaluated_elements[2]

    if not isinstance(a, (int, float)): raise TypeError(f'Invalid operator "{a}+"')
    if not isinstance(b, (int, float)): raise TypeError(f'Invalid operator "{b}"')

    if operator in ('+', 'add'):
        return a + b
    elif operator in ('-', 'sub'):
        return a - b
    elif operator in ('*', 'mul'):
        return a * b
    elif operator in ('/', 'div'):
        if b == 0:
            raise ValueError('Division by zero')
        return a / b
    elif operator in ('%', 'mod'):
        if b == 0:
            raise ValueError('Division by zero')
        return a % b
    elif operator in ('^', 'pow'):
        return a ** b
    else:
        raise ValueError(f'Invalid operator "{operator}"')


def coordinate(input_text):
    try:
        parsed_structure = parse(input_text)
        result = eval(parsed_structure)
        return result
    except Exception as e:
        return f'Error: {str(e)}'


if __name__ == '__main__':
    user = input()
    print(coordinate(user))