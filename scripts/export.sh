
if [[ "$#" -ne "5" ]]; then
    echo "Argument error"
    echo "<API key> <project_id> <spider_number> <job_id_start> <job_id_end>"
    echo "Example: bash export.sh ff5a649ffd5a69ffd5a4 12345 2 13 17"
    echo "Produces: curl -u ff5a649ffd5a69ffd5a4 \"https://storage.scrapinghub.com/items/12345/2/13?format=jl\""
    echo "                  ..."
    echo "          curl -u ff5a649ffd5a69ffd5a4 \"https://storage.scrapinghub.com/items/12345/2/17?format=jl\""
    echo "Downloads in JL format to \$PROJECT folder, and converts it to one JSON Array"
    exit
fi

APIKEY=$1
PROJECT=$2
SPIDER=$3
JOBSTART=$4
JOBEND=$5

mkdir -p $PROJECT

OUTPUT=$PROJECT/$PROJECT"_"$SPIDER".jl"
echo -n "" > $OUTPUT

for ((i = $JOBSTART ; i <= $JOBEND ; i++)); do

    curl -u $APIKEY: "https://storage.scrapinghub.com/items/$PROJECT/$SPIDER/$i?format=jl" >> $OUTPUT

done

# Join JSON Lines into one array
sed '1s/^/[/; $!s/$/,/; $s/$/]/' $OUTPUT > $PROJECT/$PROJECT"_"$SPIDER".json"