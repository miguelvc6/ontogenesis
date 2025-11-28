from typing import Any, Dict, Optional

class CodeRunner:
    """
    Executes Python code strings in a local namespace.
    WARNING: This uses `exec` and is not secure for untrusted code.
    """

    def run_code(self, code: str, entry_point: str, **kwargs) -> Any:
        """
        Executes the given code and calls the entry point function.

        Args:
            code: The Python code string to execute.
            entry_point: The name of the function to call.
            **kwargs: Arguments to pass to the entry point function.

        Returns:
            The result of the entry point function.
        """
        # Use a single dictionary for both globals and locals to ensure 
        # that functions defined in the code can access imports defined in the code.
        scope: Dict[str, Any] = {}
        
        try:
            # Execute the code definition
            exec(code, scope, scope)
        except Exception as e:
            raise RuntimeError(f"Failed to define code: {e}")

        if entry_point not in scope:
            raise ValueError(f"Entry point '{entry_point}' not found in executed code.")

        func = scope[entry_point]
        
        if not callable(func):
            raise ValueError(f"Entry point '{entry_point}' is not callable.")

        try:
            # Call the function
            return func(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to execute entry point '{entry_point}': {e}")
