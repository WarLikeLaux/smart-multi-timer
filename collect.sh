#!/bin/bash

export LANG=ru_RU.UTF-8
export LC_ALL=ru_RU.UTF-8

display_structure() {
    local output_file=$1
    shift
    local files=($(find "$@" -print0 | xargs -0))
    local root_dir=$(dirname "${files[0]}")
    local tmp_file=$(mktemp)
    printf '%s\n' "${files[@]}" | sort >"$tmp_file"
    echo "Project Structure:" | iconv -f UTF-8 -t UTF-8 >>"$output_file"
    echo >>"$output_file"
    last_dir=""
    while IFS= read -r line; do
        dir_path=$(dirname "$line")
        base_name=$(basename "$line")
        if [[ "$dir_path" != "$last_dir" ]]; then
            echo "$dir_path/" | iconv -f UTF-8 -t UTF-8 >>"$output_file"
            last_dir="$dir_path"
        fi
        echo "    $base_name" | iconv -f UTF-8 -t UTF-8 >>"$output_file"
    done <"$tmp_file"
    echo >>"$output_file"
    echo "--------------------------------" >>"$output_file"
    echo >>"$output_file"
    rm "$tmp_file"
}

process_file() {
    local file=$1
    local output_file=$2
    local san_file="${file#./}"
    local ext="${san_file##*.}"
    local basename=$(basename "$san_file")

    case "$basename" in
    'collect.log' | 'collect.sh' | 'project_source.txt' | 'composer.json' | 'composer.lock')
        echo "Skipping composer file: $file"
        return
        ;;
    esac

    case "$ext" in
    map | serialized | ico | docx | eot | ttf | otf | woff | woff2)
        echo "Skipping font file: $file"
        return
        ;;
    esac

    local encoding=$(file -bi "$file" | sed -n 's/.*charset=\([^;]*\).*/\1/p')
    if [ -z "$encoding" ]; then
        encoding="UTF-8"
    fi

    echo "File $file" | iconv -f UTF-8 -t UTF-8 >>"$output_file"
    echo >>"$output_file"

    if [ "$encoding" != "utf-8" ] && [ "$encoding" != "binary" ]; then
        iconv -f "$encoding" -t UTF-8 "$file" 2>/dev/null >>"$output_file" || cat "$file" >>"$output_file"
    else
        cat "$file" >>"$output_file"
    fi

    echo >>"$output_file"
    echo "--------------------------------" >>"$output_file"
    echo >>"$output_file"
}

process_directory() {
    local dir=$1
    local output_file=$2
    find "$dir" -type f -print0 | while IFS= read -r -d $'\0' file; do
        process_file "$file" "$output_file"
    done
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file|directory|pattern> ..." | iconv -f UTF-8 -t UTF-8
    exit 1
fi

output_file="project_source.txt"
echo -n "" >"$output_file"

display_structure "$output_file" "$@"

for item in "$@"; do
    if [ -f "$item" ]; then
        process_file "$item" "$output_file"
    elif [ -d "$item" ]; then
        process_directory "$item" "$output_file"
    else
        while IFS= read -r -d $'\0' file; do
            process_file "$file" "$output_file"
        done < <(find . -type f -name "$item" -print0)
    fi
done

echo "Project contents have been saved to $output_file" | iconv -f UTF-8 -t UTF-8
