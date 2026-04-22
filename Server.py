import socket
import threading
import time
from datetime import datetime

# Общий файл для хранения данных от всех клиентов
SHARED_FILE = "server_storage.txt"

# Создаем мьютекс (блокировку)
file_lock = threading.Lock()

# Счетчик записей (для варианта усложнения 1)
record_counter = 0
counter_lock = threading.Lock()

def write_to_shared_log(thread_id, data):
    """
    Критическая секция: запись в общий файл с использованием блокировки.
    Используется контекстный менеджер (вариант усложнения 2).
    """
    global record_counter
    
    # Получаем текущее время
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    data_size = len(data)
    
    # Формируем запись
    log_entry = f"[{timestamp}] Thread-{thread_id} | Size: {data_size} bytes | Data: {data}\n"
    
    # --- КРИТИЧЕСКАЯ СЕКЦИЯ НАЧАЛО ---
    with file_lock:  # автоматический acquire() и release() даже при ошибках
        # Имитация задержки для увеличения вероятности race condition
        time.sleep(0.05)
        
        # Запись в общий файл
        with open(SHARED_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        # --- Shared Counter (вариант усложнения 1) ---
        with counter_lock:
            record_counter += 1
            print(f"   Общий счетчик записей: {record_counter}")
    # --- КРИТИЧЕСКАЯ СЕКЦИЯ КОНЕЦ ---
    
    print(f"Поток {thread_id}: записал {data_size} байт в лог")

def handle_client(connection, address, thread_id):
    """
    Функция обработки одного клиента (выполняется в отдельном потоке).
    Получает текстовый файл от клиента и сохраняет его содержимое в общий лог.
    """
    print(f"[Поток {thread_id}] Подключен клиент: {address}")
    
    try:
        # Получаем сначала размер данных (4 байта)
        # Это более надежный способ, чем чтение до закрытия сокета
        size_data = connection.recv(4)
        if not size_data:
            connection.send(b"ERROR: No size received")
            return
        
        # Преобразуем размер из байтов в int
        data_size = int.from_bytes(size_data, byteorder='big')
        print(f"[Поток {thread_id}] Ожидается получение {data_size} байт")
        
        # Получаем данные указанного размера
        received_data = b""
        remaining = data_size
        
        while remaining > 0:
            chunk = connection.recv(min(4096, remaining))
            if not chunk:
                break
            received_data += chunk
            remaining -= len(chunk)
        
        if received_data and len(received_data) == data_size:
            # Декодируем байты в строку
            file_content = received_data.decode("utf-8")
            
            # Записываем в общий лог
            write_to_shared_log(thread_id, file_content.strip())
            
            # Отправляем подтверждение клиенту
            connection.send(b"OK: File received and logged")
            print(f"[Поток {thread_id}] Успешно получено {len(received_data)} байт")
        else:
            connection.send(f"ERROR: Expected {data_size} bytes, got {len(received_data)}".encode())
            print(f"[Поток {thread_id}] Ошибка: ожидалось {data_size} байт, получено {len(received_data)}")
            
    except socket.timeout:
        print(f"[Поток {thread_id}] Таймаут соединения с {address}")
        connection.send(b"ERROR: Timeout")
    except Exception as e:
        print(f"[Поток {thread_id}] Ошибка: {e}")
        try:
            connection.send(f"ERROR: {str(e)}".encode())
        except:
            pass
    finally:
        connection.close()
        print(f"[Поток {thread_id}] Соединение закрыто")

def start_server(host="127.0.0.1", port=12345):
    """
    Запуск многопоточного сервера.
    """
    # Инициализация общего файла
    with open(SHARED_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== SHARED LOG STARTED AT {datetime.now()} ===\n\n")
    
    # Создаем сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    print(f"Сервер запущен на {host}:{port}")
    print(f"Общий лог-файл: {SHARED_FILE}")
    print(f"Используется блокировка: threading.Lock() с контекстным менеджером")
    print("Ожидание подключений... (Ctrl+C для остановки)\n")
    
    thread_counter = 0
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            thread_counter += 1
            thread_id = thread_counter
            
            # Запускаем обработку клиента в отдельном потоке
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address, thread_id),
                daemon=True
            )
            client_thread.start()
            print(f"[Поток {thread_id}] Запущен. Активных потоков: {threading.active_count() - 1}")
            
    except KeyboardInterrupt:
        print("\nСервер остановлен пользователем")
    finally:
        server_socket.close()
        print(f"Итоговое количество записей в логе: {record_counter}")

if __name__ == "__main__":
    start_server()