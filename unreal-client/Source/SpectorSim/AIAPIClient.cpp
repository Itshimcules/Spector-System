// AIAPIClient.cpp

#include "AIAPIClient.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "JsonUtilities.h"

UAIAPIClient::UAIAPIClient()
{
}

void UAIAPIClient::SendEvent(const FGameEvent& Event)
{
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetVerb("POST");
    Request->SetURL(APIBaseURL + TEXT("/event"));
    Request->SetHeader("Content-Type", "application/json");

    // Build JSON payload
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetStringField("event_type", Event.EventType);
    JsonObject->SetStringField("action", Event.Action);
    JsonObject->SetStringField("location", Event.Location);
    JsonObject->SetNumberField("noise_level", Event.NoiseLevel);
    JsonObject->SetStringField("event_description", Event.EventDescription);

    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    Request->SetContentAsString(OutputString);
    Request->OnProcessRequestComplete().BindUObject(this, &UAIAPIClient::OnEventResponseReceived);
    Request->ProcessRequest();
}

void UAIAPIClient::RequestNPCDialogue(const FString& NPCID, const FString& PlayerMessage)
{
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetVerb("POST");
    Request->SetURL(APIBaseURL + TEXT("/dialogue"));
    Request->SetHeader("Content-Type", "application/json");

    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetStringField("npc_id", NPCID);
    JsonObject->SetStringField("player_message", PlayerMessage);

    FString OutputString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    Request->SetContentAsString(OutputString);
    Request->OnProcessRequestComplete().BindUObject(this, &UAIAPIClient::OnDialogueResponseReceived);
    Request->ProcessRequest();
}

void UAIAPIClient::OnEventResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (bWasSuccessful && Response.IsValid())
    {
        FString ResponseString = Response->GetContentAsString();
        UE_LOG(LogTemp, Log, TEXT("AI Event Response: %s"), *ResponseString);
        
        // Parse JSON and trigger NPC reactions
        // TODO: Implement NPC spawning/behavior based on response
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to send event to AI backend"));
    }
}

void UAIAPIClient::OnDialogueResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (bWasSuccessful && Response.IsValid())
    {
        FString ResponseString = Response->GetContentAsString();
        UE_LOG(LogTemp, Log, TEXT("AI Dialogue Response: %s"), *ResponseString);
        
        // Parse JSON and play audio response
        // TODO: Extract audio_base64 and play through audio component
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to get NPC dialogue"));
    }
}
