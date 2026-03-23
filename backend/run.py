#!/usr/bin/env python
"""
Workaround script to start FastAPI with Python 3.12 typing issues
This patches the typing module to prevent TypingOnly assertion errors
"""

import sys
import os

# Patch typing module to allow TypingOnly attributes
import typing
if hasattr(typing, '_SpecialForm'):
    original_init_subclass = typing._GenericAlias.__init_subclass__
    
    def patched_init_subclass(cls, **kwargs):
        # Allow additional attributes on TypingOnly classes
        if hasattr(cls, '__static_attributes__'):
            delattr(cls, '__static_attributes__')
        if hasattr(cls, '__firstlineno__'):
            delattr(cls, '__firstlineno__')
        try:
            original_init_subclass(**kwargs)
        except:
            pass
    
    typing._GenericAlias.__init_subclass__ = patched_init_subclass

# Now import uvicorn and run
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
