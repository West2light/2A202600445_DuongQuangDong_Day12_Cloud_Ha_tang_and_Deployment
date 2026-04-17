"""Mock LLM for development. Replace with OpenAI/Anthropic for production."""
import random


MOCK_RESPONSES = [
    "Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.",
    "Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.",
    "Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.",
    "Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!",
    "Microservices cho phép chia ứng dụng thành các service nhỏ độc lập, dễ scale.",
    "Graceful shutdown đảm bảo xử lý xong các in-flight requests trước khi tắt.",
]


def ask(question: str) -> str:
    """Mock LLM — trả về random response."""
    return random.choice(MOCK_RESPONSES)
