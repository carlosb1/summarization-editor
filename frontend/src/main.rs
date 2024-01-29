use log;
use serde::{Deserialize, Serialize};
use serde_json::Result;
use web_sys::wasm_bindgen::JsCast;
use web_sys::{EventTarget, HtmlInputElement};
use yew::prelude::*;

#[derive(Serialize, Deserialize)]
struct Message {
    value: String,
    typ: String,
    identifier: u64,
}

#[function_component(App)]
fn app() -> Html {
    let dialog_value = use_state(|| "".to_string());
    let counter = use_state(|| 0 as u64);
    let last_counter = use_state(|| 0 as u64);

    //TODO check how to insert this in runtime.
    let server_host: String = std::env::var("SERVER_HOST_WS").unwrap_or("0.0.0.0".to_string());
    let server_port: String = std::env::var("SERVER_PORT_WS").unwrap_or("8765".to_string());

    let address = format!("ws://{}:{}", server_host, server_port);
    log::info!("connection to server in {:?}", address);

    let mut client = wasm_sockets::EventClient::new(address.as_str())
        .expect("It was not possible to initialize the websocket");
    client.set_on_error(Some(Box::new(|error| {
        log::error!("{:#?}", error);
    })));
    client.set_on_connection(Some(Box::new(|client: &wasm_sockets::EventClient| {
        log::info!("{:#?}", client.status);
    })));
    client.set_on_close(Some(Box::new(|_evt| {
        log::info!("Connection closed");
    })));
    client.set_on_message(Some((|| {
        let dialog_value = dialog_value.clone();
        Box::new(
            move |client: &wasm_sockets::EventClient, message: wasm_sockets::Message| {
                log::info!("New Message: {:#?}", message);
                match message {
                    wasm_sockets::Message::Text(value) => {
                        let received_mess: Message = serde_json::from_str(value.as_str())
                            .expect("Message received has a incorrect format");
                        dialog_value.set(received_mess.value);
                    }
                    _ => (),
                }
            },
        )
    })()));

    let input_value_handle = use_state(String::default);
    let input_value = (*input_value_handle).clone();

    let oninput = Callback::from({
        let dialog_value = dialog_value.clone();
        let input_value_handle = input_value_handle.clone();
        let counter = counter.clone();
        move |input_event: InputEvent| {
            if let Some(content) = input_event.data() {
                let value = input_value_handle.get(0..).unwrap_or("");
                //let all_message = value.to_owned() + &content.clone();
                let all_message = value.to_owned();
                input_value_handle.set(all_message.clone());
                let messg = Message {
                    value: all_message.clone(),
                    typ: "text".to_string(),
                    identifier: *counter,
                };
                client.send_string(
                    &serde_json::to_string(&messg).expect("Message was not well built"),
                );

                counter.set(*counter + 1);
            }
        }
    });
    html! {
        <div>
                <textarea id="editor" oninput={oninput} value={input_value}></textarea>
                <textarea id="dialog" disabled=true value={(*dialog_value).clone()}> </textarea>
        </div>
    }
}

fn main() {
    wasm_logger::init(wasm_logger::Config::default());
    yew::Renderer::<App>::new().render();
}
