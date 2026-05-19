import socket
for family in (socket.AF_UNSPEC, socket.AF_INET, socket.AF_INET6):
    try:
        print('family', family, socket.getaddrinfo('db.ucrpqtplmfptmsrjcuna.supabase.co', 5432, family, socket.SOCK_STREAM))
    except Exception as exc:
        print('family', family, 'error', exc)
