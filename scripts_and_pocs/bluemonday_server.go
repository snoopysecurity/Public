package main

import (
	"log"
	"net/http"

	"github.com/microcosm-cc/bluemonday"
)

func main() {

	http.HandleFunc("/", handler)
	http.ListenAndServe(":8080", nil)
}

func handler(w http.ResponseWriter, r *http.Request) {
	p := bluemonday.UGCPolicy()
	keys, ok := r.URL.Query()["key"]

	if !ok || len(keys[0]) < 1 {
		log.Println("Url Param 'key' is missing")
		return
	}

	// Query()["key"] will return an array of items,
	// we only want the single item.
	key := keys[0]
	w.Write([]byte(`
    <!doctype html>
    <html>
      <head>
        <title>This is the title of the webpage!</title>
      </head>
      <body>
      `))
	w.Write([]byte("Url Param 'key' is: " + p.Sanitize(string(key))))
	w.Write([]byte(`
    </body>
    </html>
      `))
	log.Println("Url Param 'key' is: " + string(key))
}
