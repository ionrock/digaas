ZONE_FILE_DIR=$1
if [ -z "$ZONE_FILE_DIR" ]; then
    echo "Usage: $0 <zone-file-dir>"
    echo "(zone file dir is probably /var/cache/bind)"
    exit 1
fi

NZF=`ls $ZONE_FILE_DIR | grep "[.]nzf$"`
if [ ! -z "$NZF" ]; then
    NZF=$ZONE_FILE_DIR/$NZF
    rm $NZF && touch $NZF && chown bind:bind $NZF
fi

rm -f $ZONE_FILE_DIR/slave.*
rm -f $ZONE_FILE_DIR/*.zone

service bind9 restart

rndc status
