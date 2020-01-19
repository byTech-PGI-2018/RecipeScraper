
MAXARG=6

if [[ "$#" -lt "$MAXARG" ]]; then
    echo "Argument error"
    echo "<API key> <project_id> <spider_name> <page_start> <page_end> <page_increment> [arg1, arg2, ...]"
    echo "Example: bash export.sh ff5a649ffd5a69ffd5a4 12345 my_spider 1 60 10"
    echo "Other arguments will be passed as additional spider arguments"
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

# Increment initial end offset by $INCREMENT-1
((INITIALINC-=1))
((PAGEEND+=INITIALINC))

while true; do
    # Pageend is set to $PAGEEND if it's smaller than $TOTAL, otherwise, it's set to $TOTAL
    COMMAND="curl -u $APIKEY: https://app.scrapinghub.com/api/run.json -d project=$PROJECT -d spider=$SPIDER -d priority=0 -d pagestart=$PAGESTART -d pageend=$([ "$PAGEEND" -ge "$TOTAL" ] && echo "$TOTAL" || echo "$PAGEEND")"

    # If there are any additional spider arguments, append them to final curl command
    for ((i = ((MAXARG+1)); i <= $#; i++ )); do
        COMMAND=$COMMAND" -d "${!i}
    done

    # Run curl command
    $COMMAND

    # Check if we have searched max number of pages
    if [[ $PAGEEND -ge $TOTAL ]]; then
        break
    fi

    # Increase page index offsets by value passed as argument
    ((PAGESTART+=INCREMENT))
    ((PAGEEND+=INCREMENT))

    # Prevent making too many requests in a short amount of time
    sleep 3

done