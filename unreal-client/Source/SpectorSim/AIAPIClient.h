// AIAPIClient.h - C++ class for low-latency AI backend communication

#pragma once

#include "CoreMinimal.h"
#include "Http.h"
#include "Json.h"
#include "AIAPIClient.generated.h"

USTRUCT(BlueprintType)
struct FGameEvent
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite)
    FString EventType;

    UPROPERTY(BlueprintReadWrite)
    FString Action;

    UPROPERTY(BlueprintReadWrite)
    FString Location;

    UPROPERTY(BlueprintReadWrite)
    int32 NoiseLevel;

    UPROPERTY(BlueprintReadWrite)
    FString EventDescription;
};

UCLASS(BlueprintType)
class SPECTORSIM_API UAIAPIClient : public UObject
{
    GENERATED_BODY()

public:
    UAIAPIClient();

    UFUNCTION(BlueprintCallable, Category = "AI")
    void SendEvent(const FGameEvent& Event);

    UFUNCTION(BlueprintCallable, Category = "AI")
    void RequestNPCDialogue(const FString& NPCID, const FString& PlayerMessage);

    UPROPERTY(BlueprintReadWrite, Category = "AI")
    FString APIBaseURL = TEXT("http://localhost:8000");

private:
    void OnEventResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    void OnDialogueResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
};
