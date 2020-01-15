

if [[ "$#" -ne "5" ]]; then
    echo "Argument error"
    echo "<API key> <project_id> <spider_name> <page_start> <page_end>"
    echo "Example: bash export.sh ff5a649ffd5a69ffd5a4 12345 my_spider 1 60"
    exit
fi

APIKEY=$1
PROJECT=$2
SPIDER=$3
PAGESTART=$4
PAGEEND=$4
TOTAL=$5

((PAGEEND+=19))

while true; do

    if [[ $PAGEEND -ge $TOTAL ]]; then
        echo "curl -u $APIKEY: \"https://app.scrapinghub.com/api/run.json\" -d project=$PROJECT -d spider=$SPIDER -d pagestart=$PAGESTART -d pageend=$TOTAL"
        break
    fi

    echo "curl -u $APIKEY: \"https://app.scrapinghub.com/api/run.json\" -d project=$PROJECT -d spider=$SPIDER -d pagestart=$PAGESTART -d pageend=$PAGEEND"

    ((PAGESTART+=20))
    ((PAGEEND+=20))

    sleep 3

done