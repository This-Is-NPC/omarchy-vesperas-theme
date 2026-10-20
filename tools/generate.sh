#!/usr/bin/env bash
# Usage: tools/generate.sh <prompt-file> [reference-image...]
# MODEL overrides the default image model.
set -euo pipefail
cd "$(dirname "$0")/.."
source .env

prompt_file=$1
model=${MODEL:-openai/gpt-image-2.5-sunburst}
name=$(basename "$prompt_file" .txt)
out="drafts/${name}-$(date +%Y%m%d-%H%M%S)"

references=$(mktemp)
trap 'rm -f "$references"' EXIT
echo '[]' >"$references"
for reference in "${@:2}"; do
  if [[ ! -f $reference ]]; then
    echo "reference not found: $reference" >&2
    exit 1
  fi
  mime=$(file -b --mime-type "$reference")
  jq --rawfile data <(base64 -w0 "$reference") --arg mime "$mime" \
    '. + [{type: "image_url", image_url: {url: "data:\($mime);base64,\($data)"}}]' \
    "$references" >"$references.next"
  mv "$references.next" "$references"
done

jq -n --arg model "$model" --rawfile prompt "$prompt_file" --slurpfile refs "$references" '{
  model: $model,
  prompt: $prompt,
  aspect_ratio: "16:9",
  n: 1
} + (if $refs[0] == [] then {} else {input_references: $refs[0]} end)' |
  curl -sS https://openrouter.ai/api/v1/images \
    -H "Authorization: Bearer $OPENROUTER_KEY" \
    -H "Content-Type: application/json" \
    -d @- >"$out.json"

b64=$(jq -r '.data[0].b64_json // empty' "$out.json")
if [[ -z $b64 ]]; then
  jq '.error // .' "$out.json" >&2
  exit 1
fi
ext=$(jq -r '.data[0].media_type // "image/png" | sub("image/"; "") | sub("jpeg"; "jpg")' "$out.json")
base64 -d <<<"$b64" >"$out.$ext"
magick "$out.$ext" -filter Lanczos -resize 3840x2160^ -gravity center -extent 3840x2160 -quality 95 "$out-4k.jpg"
jq '.usage.cost' "$out.json"
echo "$out-4k.jpg"
