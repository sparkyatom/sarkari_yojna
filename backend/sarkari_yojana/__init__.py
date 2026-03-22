# FIX: Install PyMySQL as MySQLdb fallback for environments where mysqlclient
# cannot be compiled (e.g. Windows without Visual C++ build tools).
# If mysqlclient is installed, this block is simply never reached.
try:
    import MySQLdb  # noqa: F401  — mysqlclient is available, nothing to do
except ImportError:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass  # Neither driver present — Django will raise a clear error at startup
