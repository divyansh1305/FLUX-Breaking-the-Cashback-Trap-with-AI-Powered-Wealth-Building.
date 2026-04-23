try:
    from NorenRestApiPy.NorenApi import NorenApi
    import pyotp
    print("SUCCESS: Shoonya libraries are installed.")
except ImportError as e:
    print(f"MISSING: {e}")
