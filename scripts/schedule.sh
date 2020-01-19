

if [[ "$#" -ne "6" ]]; then
    echo "Argument error"
    echo "<API key> <project_id> <spider_name> <page_start> <page_end> <increment>"
    echo "Example: bash export.sh ff5a649ffd5a69ffd5a4 12345 my_spider 1 60 10"
    exit
fi

APIKEY=$1
PROJECT=$2
SPIDER=$3
PAGESTART=$4
PAGEEND=$4
TOTAL=$5
INCREMENT=$6
INITIALINC=$6

((INITIALINC-=1))
((PAGEEND+=INITIALINC))

while true; do

    if [[ $PAGEEND -ge $TOTAL ]]; then
        curl -u $APIKEY: "https://app.scrapinghub.com/api/run.json" -d project=$PROJECT -d spider=$SPIDER -d priority=0 -d pagestart=$PAGESTART -d pageend=$TOTAL
        break
    fi

    curl -u $APIKEY: "https://app.scrapinghub.com/api/run.json" -d project=$PROJECT -d spider=$SPIDER -d priority=0 -d pagestart=$PAGESTART -d pageend=$PAGEEND

    ((PAGESTART+=INCREMENT))
    ((PAGEEND+=INCREMENT))

    sleep 3

done