FROM alpine:latest
LABEL maintainer="Tuan Nguyen Huu <tuan.nguyenhuu@qtetech.com.vn>"
WORKDIR /archive
# Đảm bảo 2 file này đã có sẵn trong repo GitHub
COPY product-E-05-04-2026.csv .
COPY product-V-05-04-2026.csv .
CMD ["echo", "QTE Technologies Industrial MRO Archive 2026 Loaded."]
