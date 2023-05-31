// ������Ҫ��ͷ�ļ�
#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include <fstream>
#include <sstream>
#include <tobii/tobii.h>
#include <tobii/tobii_streams.h>
#include <stdio.h>
#include <assert.h>
#include <winsock2.h> // Windows�µ��׽��ֿ�
#include <WS2tcpip.h>
#pragma comment(lib, "Ws2_32.lib") // �����׽��ֿ�

using namespace std;

// ������Ҫ��ͷ�ļ�
FILE* fp;
int sockfd, newsockfd, portno = 5001; // �׽�����ر���
socklen_t clilen;
char buffer[256];
struct sockaddr_in serv_addr, cli_addr;

// gaze point ���ݻص��������� gaze point ���ݿ���ʱ���á�
// ����ص������� tobii_gaze_point_subscribe() ȷ����
void gaze_point_callback(tobii_gaze_point_t const* gaze_point, void* user_data)
{
    // д�� gaze point ���ݵ��ļ�
    if (fp != nullptr)
    {
        fprintf(fp, "%d, %lld, %f, %f\n", gaze_point->validity, gaze_point->timestamp_us, gaze_point->position_xy[0], gaze_point->position_xy[1]);
    }

    // �������ݵ��ͻ���
    // �� gaze point ����תΪ�ַ�����ͨ���׽��ַ��͸��ͻ��ˡ�
    sprintf(buffer, "%d,%lld,%f,%f,", gaze_point->validity, gaze_point->timestamp_us, gaze_point->position_xy[0], gaze_point->position_xy[1]);
    send(newsockfd, buffer, strlen(buffer), 0);
}

// Device URL ���պ������� tobii_enumerate_local_device_urls() ִ�гɹ������øú�����
// �ú�����ȡ��һ�� Device URL�������浽 buffer �С�
static void url_receiver(char const* url, void* user_data)
{
    char* buffer = (char*)user_data;
    if (*buffer != '\0') return; // ֻ�����һ�� Device URL

    if (strlen(url) < 256)
        strcpy(buffer, url);
}

int main(int argc, char* argv[])
{
    // ������ Tobii ��ش���
    tobii_api_t* api;
    tobii_error_t error = tobii_api_create(&api, NULL, NULL);
    assert(error == TOBII_ERROR_NO_ERROR);

    char url[256] = { 0 };
    error = tobii_enumerate_local_device_urls(api, url_receiver, url); // ��ȡ��һ���豸�� URL
    assert(error == TOBII_ERROR_NO_ERROR && *url != '\0');

    tobii_device_t* device;
    error = tobii_device_create(api, url, &device); // ͨ���豸�� URL �����豸ʵ��
    assert(error == TOBII_ERROR_NO_ERROR);

    error = tobii_gaze_point_subscribe(device, gaze_point_callback, 0); // ���� gaze point ������
    assert(error == TOBII_ERROR_NO_ERROR);

    // �������ļ���ش���
    const char* filename = "./data/gaze_data_%02d.csv";
    char buf[100];
    fp = fopen("./data/gaze_data_01.csv", "r");
    if (fp == nullptr) {
        // �ļ������ڣ�ʹ��"gaze_data_01.csv"��Ϊ�ļ���
        sprintf(buf, filename, 1);
    }
    else {
        // �ļ����ڣ�ʹ�õ��������ֺ�׺
        fclose(fp);

        int i = 2;
        do {
            sprintf(buf, filename, i++);
        } while (fopen(buf, "r") != nullptr);
    }

    fp = fopen(buf, "a");

    // �������׽�����ش���
    WSADATA wsaData;
    int iResult = WSAStartup(MAKEWORD(2, 2), &wsaData); // ��ʼ���׽��ֿ�
    if (iResult != 0) {
        printf("WSAStartup failed: %d\n", iResult);
        return 1;
    }

    sockfd = socket(AF_INET, SOCK_STREAM, 0); // �����׽���
    if (sockfd == INVALID_SOCKET) {
        printf("ERROR opening socket: %ld\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }

    // �� IP �� Port
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);

    if (bind(sockfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR) {
        printf("ERROR on binding: %ld\n", WSAGetLastError());
        closesocket(sockfd);
        WSACleanup();
        return 1;
    }

    // �����׽��֣��ȴ��ͻ�������
    if (listen(sockfd, 5) == SOCKET_ERROR) {
        printf("ERROR on listen: %ld\n", WSAGetLastError());
        closesocket(sockfd);
        WSACleanup();
        return 1;
    }

    clilen = sizeof(cli_addr);
    newsockfd = accept(sockfd, (struct sockaddr*)&cli_addr, &clilen); // ���տͻ�����������
    if (newsockfd == INVALID_SOCKET) {
        printf("ERROR on accept: %ld\n", WSAGetLastError());
        closesocket(sockfd);
        WSACleanup();
        return 1;
    }

    int is_running = 10000; // �ڴ�ʾ���У�ѭ��ִ��һ��������ֹͣ
    while (--is_running > 0)
    {
        // �ȴ������� Tobii �ص�
        error = tobii_wait_for_callbacks(NULL, 1, &device);
        assert(error == TOBII_ERROR_NO_ERROR || error == TOBII_ERROR_TIMED_OUT);

        error = tobii_device_process_callbacks(device);
        assert(error == TOBII_ERROR_NO_ERROR);
    }

    // �ͷ���Դ
    error = tobii_gaze_point_unsubscribe(device);
    assert(error == TOBII_ERROR_NO_ERROR);

    error = tobii_device_destroy(device);
    assert(error == TOBII_ERROR_NO_ERROR);

    error = tobii_api_destroy(api);
    assert(error == TOBII_ERROR_NO_ERROR);

    fclose(fp);
    closesocket(newsockfd);
    closesocket(sockfd);
    WSACleanup();

    return 0;
}