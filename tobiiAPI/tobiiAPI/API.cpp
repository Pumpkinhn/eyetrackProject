// 引入需要的头文件
#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include <fstream>
#include <sstream>
#include <tobii/tobii.h>
#include <tobii/tobii_streams.h>
#include <stdio.h>
#include <assert.h>
#include <winsock2.h> // Windows下的套接字库
#include <WS2tcpip.h>
#pragma comment(lib, "Ws2_32.lib") // 引入套接字库

using namespace std;

// 引入需要的头文件
FILE* fp;
int sockfd, newsockfd, portno = 5001; // 套接字相关变量
socklen_t clilen;
char buffer[256];
struct sockaddr_in serv_addr, cli_addr;

// gaze point 数据回调函数，当 gaze point 数据可用时调用。
// 具体回调规则由 tobii_gaze_point_subscribe() 确定。
void gaze_point_callback(tobii_gaze_point_t const* gaze_point, void* user_data)
{
    // 写入 gaze point 数据到文件
    if (fp != nullptr)
    {
        fprintf(fp, "%d, %lld, %f, %f\n", gaze_point->validity, gaze_point->timestamp_us, gaze_point->position_xy[0], gaze_point->position_xy[1]);
    }

    // 发送数据到客户端
    // 将 gaze point 数据转为字符串后，通过套接字发送给客户端。
    sprintf(buffer, "%d,%lld,%f,%f,", gaze_point->validity, gaze_point->timestamp_us, gaze_point->position_xy[0], gaze_point->position_xy[1]);
    send(newsockfd, buffer, strlen(buffer), 0);
}

// Device URL 接收函数，当 tobii_enumerate_local_device_urls() 执行成功后会调用该函数。
// 该函数获取第一个 Device URL，并保存到 buffer 中。
static void url_receiver(char const* url, void* user_data)
{
    char* buffer = (char*)user_data;
    if (*buffer != '\0') return; // 只保存第一个 Device URL

    if (strlen(url) < 256)
        strcpy(buffer, url);
}

int main(int argc, char* argv[])
{
    // 以下是 Tobii 相关代码
    tobii_api_t* api;
    tobii_error_t error = tobii_api_create(&api, NULL, NULL);
    assert(error == TOBII_ERROR_NO_ERROR);

    char url[256] = { 0 };
    error = tobii_enumerate_local_device_urls(api, url_receiver, url); // 获取第一个设备的 URL
    assert(error == TOBII_ERROR_NO_ERROR && *url != '\0');

    tobii_device_t* device;
    error = tobii_device_create(api, url, &device); // 通过设备的 URL 创建设备实例
    assert(error == TOBII_ERROR_NO_ERROR);

    error = tobii_gaze_point_subscribe(device, gaze_point_callback, 0); // 订阅 gaze point 数据流
    assert(error == TOBII_ERROR_NO_ERROR);

    // 以下是文件相关代码
    const char* filename = "./data/gaze_data_%02d.csv";
    char buf[100];
    fp = fopen("./data/gaze_data_01.csv", "r");
    if (fp == nullptr) {
        // 文件不存在，使用"gaze_data_01.csv"作为文件名
        sprintf(buf, filename, 1);
    }
    else {
        // 文件存在，使用递增的数字后缀
        fclose(fp);

        int i = 2;
        do {
            sprintf(buf, filename, i++);
        } while (fopen(buf, "r") != nullptr);
    }

    fp = fopen(buf, "a");

    // 以下是套接字相关代码
    WSADATA wsaData;
    int iResult = WSAStartup(MAKEWORD(2, 2), &wsaData); // 初始化套接字库
    if (iResult != 0) {
        printf("WSAStartup failed: %d\n", iResult);
        return 1;
    }

    sockfd = socket(AF_INET, SOCK_STREAM, 0); // 创建套接字
    if (sockfd == INVALID_SOCKET) {
        printf("ERROR opening socket: %ld\n", WSAGetLastError());
        WSACleanup();
        return 1;
    }

    // 绑定 IP 和 Port
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

    // 监听套接字，等待客户端连接
    if (listen(sockfd, 5) == SOCKET_ERROR) {
        printf("ERROR on listen: %ld\n", WSAGetLastError());
        closesocket(sockfd);
        WSACleanup();
        return 1;
    }

    clilen = sizeof(cli_addr);
    newsockfd = accept(sockfd, (struct sockaddr*)&cli_addr, &clilen); // 接收客户端连接请求
    if (newsockfd == INVALID_SOCKET) {
        printf("ERROR on accept: %ld\n", WSAGetLastError());
        closesocket(sockfd);
        WSACleanup();
        return 1;
    }

    int is_running = 10000; // 在此示例中，循环执行一定次数后停止
    while (--is_running > 0)
    {
        // 等待、处理 Tobii 回调
        error = tobii_wait_for_callbacks(NULL, 1, &device);
        assert(error == TOBII_ERROR_NO_ERROR || error == TOBII_ERROR_TIMED_OUT);

        error = tobii_device_process_callbacks(device);
        assert(error == TOBII_ERROR_NO_ERROR);
    }

    // 释放资源
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