class Calculator:
    """
    A simple calculator class that can perform basic arithmetic operations.
    """
    
    def __init__(self, name="Calculator"):
        """
        Initialize the calculator with a name.
        
        Args:
            name (str): Name of the calculator instance
        """
        self.name = name
        self.history = []
        print(f"{self.name} initialized successfully!")
    
    def add(self, a: float, b: float) -> float:
        """
        Add two numbers.
        
        Args:
            a (float): First number
            b (float): Second number
            
        Returns:
            float: Sum of a and b
        """
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """
        Subtract b from a.
        
        Args:
            a (float): First number
            b (float): Second number
            
        Returns:
            float: Difference of a and b
        """
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """
        Multiply two numbers.
        
        Args:
            a (float): First number
            b (float): Second number
            
        Returns:
            float: Product of a and b
        """
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """
        Divide a by b.
        
        Args:
            a (float): Numerator
            b (float): Denominator
            
        Returns:
            float: Quotient of a and b
            
        Raises:
            ValueError: If b is zero
        """
        if b == 0:
            raise ValueError("Cannot divide by zero!")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def print_range(self, start: int, end: int, step: int = 1):
        """
        Print a range of numbers.
        
        Args:
            start (int): Starting number
            end (int): Ending number (exclusive)
            step (int): Step size (default: 1)
        """
        print(f"{self.name} printing range from {start} to {end} with step {step}:")
        for i in range(start, end, step):
            print(i, end=" ")
        print()  # New line at the end
    
    def get_history(self) -> list:
        """
        Get the calculation history.
        
        Returns:
            list: List of previous calculations
        """
        return self.history.copy()
    
    def clear_history(self):
        """Clear the calculation history."""
        self.history.clear()
        print(f"{self.name} history cleared!")
    
    def __str__(self) -> str:
        """String representation of the calculator."""
        return f"{self.name} (History: {len(self.history)} calculations)"


# Example usage when run directly
if __name__ == "__main__":
    # Create a calculator instance
    calc = Calculator("My Calculator")
    
    # Test some operations
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")
    
    # Print a range
    calc.print_range(1, 11, 2)
    
    # Show history
    print("\nCalculation history:")
    for calculation in calc.get_history():
        print(f"  {calculation}") 