#!/bin/bash
# 테스트용 오디오 픽스처 생성 스크립트
# 요구사항: ffmpeg 설치 필요 (brew install ffmpeg)

FIXTURES_DIR="$(dirname "$0")/sample_audio"
mkdir -p "$FIXTURES_DIR"

# 3초 무음 m4a 생성
if [ ! -f "$FIXTURES_DIR/silence_3s.m4a" ]; then
    ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 3 -c:a aac "$FIXTURES_DIR/silence_3s.m4a"
    echo "생성됨: silence_3s.m4a"
fi

# 3초 무음 mp4 생성 (오디오만 포함)
if [ ! -f "$FIXTURES_DIR/silence_3s.mp4" ]; then
    ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 3 -c:a aac "$FIXTURES_DIR/silence_3s.mp4"
    echo "생성됨: silence_3s.mp4"
fi

echo "픽스처 생성 완료: $FIXTURES_DIR"
