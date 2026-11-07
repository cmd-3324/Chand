def add(a, b):
    return a + b 
    # If function returns False, It will count on it as an error. Assert Has : expression, OptionalErrorMessage

def test_add():
    assert add(2, 3) == 5
    
