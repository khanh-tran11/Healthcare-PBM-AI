# Dùng kiến thức khóa học cho dự án (không tốn thêm thời gian code)

Khóa học có 5 phần: Enterprise Design Thinking, AI agents, RAG, multiagent systems và IBM Bob. Ý chính: đưa đúng ngôn ngữ của khóa học vào README, slide và lúc pitch, vì giám khảo IBM sẽ nhận ra ngay.

## 1. Enterprise Design Thinking (dùng cho Design và Effectiveness)

### Problem statement (công thức trong khóa: "Our users struggle to achieve some task today because of blocks")
> Người Việt trung niên và cao tuổi gặp khó khăn khi phân biệt tin sức khỏe thật giả trên Facebook và Zalo, vì tin giả dùng đúng cách nói dân gian quen thuộc của họ, còn nguồn chính thống thì dài, khó tìm và dùng thuật ngữ y khoa.

Khóa học nhấn mạnh: không nhắc tới giải pháp trong problem statement, và phải nêu đích danh người dùng. Câu trên làm đúng cả hai điều đó.

### Hill (Who / What / Wow), slide 1 và đầu README
- **Who:** bà Hoa, 66 tuổi, và con cháu như Minh, 24 tuổi.
- **What:** dán một tin nhận được trên Zalo và trong vài giây biết tin đó đúng, sai hay gây hiểu lầm, kèm nguồn Bộ Y tế hoặc WHO, bằng chính cách nói của mình.
- **Wow (đo được):** chính xác X% trên 20 claim, trả lời trong Y giây, Z đồng mỗi lần; mỗi kết luận đều có nguồn.

X, Y, Z lấy từ `eval/ablation.md`. Khóa học nói Wow phải đo được, nên đây chính là chỗ đặt bảng ablation.

### Empathy map của bà Hoa (Says / Thinks / Does / Feels), 1 slide hoặc mục README
| Says | Thinks |
|---|---|
| "Bài thuốc gia truyền này hàng xóm dùng khỏi rồi" | "Đi viện tốn tiền, làm phiền con" |
| **Does** | **Feels** |
| Chuyển tiếp video vào nhóm Zalo gia đình, mua thuốc online | Lo bệnh, tin người quen hơn bác sĩ trên mạng |

Nguồn dẫn chứng là các ca trên VietNamNet (07 và 08/2025) đã có trong plan.

### As-is và To-be (1 slide, 2 cột)
- **As-is:** bà Hoa nhận video, tin và chuyển tiếp. Minh thấy nhưng ngại đính chính (chỉ 16,2% người trẻ dám đính chính).
- **To-be:** Minh hoặc bà Hoa dán tin vào tool, đọc thẻ "Sai" kèm dòng "Đã hiểu: tai biến → đột quỵ", rồi bấm "Copy gửi gia đình" để gửi lại lời giải thích lịch sự, có nguồn.

### Ba nguyên tắc của EDT, mỗi nguyên tắc một câu khi pitch
- **Focus on user outcomes:** UI chữ to, nói bằng ngôn ngữ dân gian, nút copy.
- **Restless reinvention:** mỗi cải tiến đều đo lại bằng eval (bảng ablation chính là vòng lặp Observe, Reflect, Make).
- **Diverse empowered teams:** Khanh lo phần AI, Link lo dữ liệu và UX, Bob viết code, hai bạn duyệt.

### Playback
Khóa học gọi bài trình bày dạng kể chuyện là Playback. Đặt tên phần pitch là "Playback" và mở đầu bằng câu chuyện bà Hoa, không mở bằng kiến trúc.

### Sponsor User
Không có thời gian phỏng vấn người dùng thật. Đưa vào slide roadmap: "Bước tiếp theo: 5 Sponsor User là người cao tuổi dùng thử trong 2 tuần". Nói thật giới hạn này sẽ được điểm hơn là bỏ qua.

## 2. AI agents (dùng cho Completeness và Creativity)

Khóa học mô tả agent qua 5 bước: perceive, process, decide, act, learn. Map vào graph LangGraph trong Prompt K3:

| Bước của khóa học | Node trong dự án |
|---|---|
| Perceive | Nhận claim, chuẩn hóa từ dân gian (`folk.normalize`) |
| Process | Hybrid retrieval từ nguồn Bộ Y tế, WHO |
| Decide | LLM judge chọn nhãn và mức tin cậy |
| Act | Trả thẻ kết quả + lời nhắn gửi gia đình |
| Learn | Vòng `check`: không đủ bằng chứng thì mở rộng truy vấn và tìm lại; về lâu dài thì eval set lớn dần |

Loại agent theo khóa học: đây là **goal-based agent**, với mục tiêu "chỉ kết luận khi có nguồn". Nói đúng chữ này khi giám khảo hỏi.

## 3. RAG (dùng cho Completeness)

Khóa học chia RAG thành 5 bước. Đưa đúng 5 tên này vào sơ đồ README:
1. Prompt creation: claim của người dùng, đã chuẩn hóa từ dân gian.
2. Information search: BM25 + vector trên watsonx embeddings.
3. Information retrieval: top 5 đoạn, gộp bằng RRF.
4. Prompt augmentation: ghép đoạn nguồn vào prompt judge.
5. Response generation: watsonx LLM trả JSON có trích dẫn.

Lợi ích theo khóa học, dùng làm câu trả lời "vì sao RAG mà không fine-tune": cập nhật kiến thức không cần train lại, tăng niềm tin nhờ có nguồn, rẻ hơn khi scale. Riêng ý "thêm chủ đề chỉ cần thêm file nguồn" là câu trả lời cho phần Scale.

## 4. Multiagent systems (chỉ dùng khi pitch, không build thêm)

Nói trung thực: sản phẩm là một agent nhiều bước. Câu chuyện multiagent nằm ở cách xây dựng và ở roadmap:
- **Lúc build:** Bob (agent viết code) và Claude (agent lập kế hoạch, review) phối hợp theo vai trò, còn người duyệt mỗi bước. Đây đúng là kiểu "role-based collaboration" trong khóa học.
- **Roadmap:** tách thành các agent có vai trò riêng (agent chuẩn hóa, agent tìm nguồn, agent kiểm tra an toàn bằng Granite Guardian), điều phối bằng watsonx Orchestrate, giống ví dụ Email, Sourcing và Compliance Agent trong khóa học.

## 5. IBM Bob (dùng cho Completeness: "clear application of IBM technology")

Khóa học chia cách dùng Bob theo các giai đoạn SDLC: Understanding, Planning, Building, Improving, Documenting. Chụp màn hình mỗi giai đoạn rồi đặt vào README mục "Built with IBM Bob":

| Giai đoạn SDLC | Đã làm gì với Bob | Prompt |
|---|---|---|
| Understanding | Ask mode: "Explain this watsonx error" khi smoke test lỗi | K1 |
| Planning | Plan mode tạo khung dự án | K1 |
| Building | Agent mode viết RAG, eval, UI | K2, K3, L1, L2 |
| Improving | `/review` + sửa lỗi; troubleshoot khi eval hỏng (giống lab "Troubleshoot your code") | K4 |
| Documenting | Bob viết README và test | K4 |

## Thứ tự làm (không ảnh hưởng lịch 90 phút)
- **Trong lúc Bob chạy K2 và K3:** Khanh dán Problem statement, Hill, Empathy map và As-is/To-be vào slide. Chỉ cần chép, mất khoảng 5 phút.
- **Prompt K4:** đã thêm yêu cầu để README có Hill, problem statement, 5 bước RAG và bảng SDLC với Bob.
- **Pitch:** gọi tên các khái niệm của khóa học (Hill, Playback, goal-based agent, 5 bước RAG) ít nhất một lần mỗi khái niệm.
