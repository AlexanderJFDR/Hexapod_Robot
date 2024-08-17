/*
	单片机：STM32F103RCT6/STM32F103C8T6  倍频 72M 
	
	逻辑：
	初始化：串口1 2 3初始化，1 2为全双工串口，3为总线串口，即单线通信 
	主循环：隔10秒调用一次动作组
*/
#include "stm32f10x_conf.h"
#define tb_interrupt_open() {__enable_irq();}	//总中断打开
#define TB_USART1_COM 1
#define TB_USART2_COM 2
#define TB_USART3_COM 3

#define TB_USART_FLAG_ERR  0X0F
#define TB_USART_FLAG_RXNE 0X20
#define TB_USART_FLAG_TXE  0X80

#define tb_interrupt_open() {__enable_irq();}

#define uart1_open() 	{USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);}
#define uart1_close() 	{USART_ITConfig(USART1, USART_IT_RXNE, DISABLE);}

#define uart2_open() 	{USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);}		
#define uart2_close() 	{USART_ITConfig(USART2, USART_IT_RXNE, DISABLE);}		

#define uart3_open() 	{USART_ITConfig(USART3, USART_IT_RXNE, ENABLE);}		
#define uart3_close() 	{USART_ITConfig(USART3, USART_IT_RXNE, DISABLE);}		

void tb_usart_init(void);
void tb_usart1_init(u32 rate);
void tb_usart2_init(u32 rate);
void tb_usart3_init(u32 rate);

void tb_usart1_send_byte(u8 Data);
void tb_usart1_send_nbyte(u8 *Data, u16 size);
void tb_usart1_send_str(u8 *Data);

void tb_usart2_send_byte(u8 Data);
void tb_usart2_send_nbyte(u8 *Data, u16 size);
void tb_usart2_send_str(u8 *Data);

void tb_usart3_send_byte(u8 Data);
void tb_usart3_send_nbyte(u8 *Data, u16 size);
void tb_usart3_send_str(u8 *Data);

int tb_usart1_interrupt(void);
int tb_usart2_interrupt(void);
int tb_usart3_interrupt(void);

void uart1_send_str(u8 *str);
void uart1_send_nbyte(u8 *Data, u16 size);
void uart1_send_byte(u8 data);

void uart2_send_str(u8 *str);
void uart2_send_nbyte(u8 *Data, u16 size);
void uart2_send_byte(u8 data);

void zx_uart_send_str(u8 *str);
void uart3_send_str(u8 *str);
void uart3_send_nbyte(u8 *Data, u16 size);
void uart3_send_byte(u8 data);


void rcc_init(void);							//主频设置
void delay_ms(unsigned int t);		//毫秒级别延时


int main(void) {	
	rcc_init();				//主频设置72M
	tb_usart_init();		//初始化串口
	tb_interrupt_open();	//总中断打开
	while(1) {	
		uart1_send_str((u8 *)"$DGT:0-4,1!");	//串口1 调用 0到4 动作，执行1次 其他命令参照控制器指令
		zx_uart_send_str((u8 *)"$DGT:0-4,1!");	//总线口 调用 0到4 动作，执行1次 其他命令参照控制器指令
		delay_ms(10000);						//延时10秒	
	}
}

void rcc_init(void) {
	ErrorStatus HSEStartUpStatus;
	RCC_DeInit();
	RCC_HSEConfig(RCC_HSE_ON); 
	HSEStartUpStatus = RCC_WaitForHSEStartUp();
	while(HSEStartUpStatus == ERROR);
	RCC_HCLKConfig(RCC_SYSCLK_Div1);//SYSCLK
	RCC_PCLK1Config(RCC_HCLK_Div2);//APB1  MAX = 36M
	RCC_PCLK2Config(RCC_HCLK_Div1);//APB2  MAX = 72M
	RCC_PLLConfig(RCC_PLLSource_HSE_Div1, RCC_PLLMul_9);
	RCC_PLLCmd(ENABLE); 
	while(RCC_GetFlagStatus(RCC_FLAG_PLLRDY) == RESET);
	RCC_SYSCLKConfig(RCC_SYSCLKSource_PLLCLK);
	while(RCC_GetSYSCLKSource() != 0x08);
}


void delay_ms(unsigned int t) {
	int t1;
	while(t--) {
		t1 = 7200;
		while(t1--);
	}
}

void tb_usart_init(void) {
	tb_usart1_init(115200);
	uart1_open();
	
	tb_usart2_init(115200);
	uart2_open();
	
	tb_usart3_init(115200);
	uart3_open();
	
	tb_interrupt_open();
	return;
}


void tb_usart1_init(u32 rate) {  
    GPIO_InitTypeDef GPIO_InitStructure;  
    USART_InitTypeDef USART_InitStructure; 
	USART_ClockInitTypeDef USART_ClockInitStructure; 	
    NVIC_InitTypeDef NVIC_InitStructure;  
  
	
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_USART1, ENABLE);  
    USART_DeInit(USART1);  
    /* Configure USART Tx as alternate function push-pull */  
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_9;  
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;  
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;  
    GPIO_Init(GPIOA, &GPIO_InitStructure);  
      
    /* Configure USART Rx as input floating */  
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;  
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;  
    GPIO_Init(GPIOA, &GPIO_InitStructure);  
  
    USART_InitStructure.USART_BaudRate = rate;  
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;  
    USART_InitStructure.USART_StopBits = USART_StopBits_1;  
    USART_InitStructure.USART_Parity = USART_Parity_No;  
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;  
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;  
    
	USART_ClockInitStructure.USART_Clock = USART_Clock_Disable;  
    USART_ClockInitStructure.USART_CPOL = USART_CPOL_Low;  
    USART_ClockInitStructure.USART_CPHA = USART_CPHA_2Edge;  
    USART_ClockInitStructure.USART_LastBit = USART_LastBit_Disable;  
    USART_ClockInit(USART1, &USART_ClockInitStructure);  
	USART_Init(USART1, &USART_InitStructure );   
  
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_0);
    NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;  
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;  
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;  
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;  
    NVIC_Init(&NVIC_InitStructure); 
	
	USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
    //USART_ITConfig(USART1, USART_IT_TXE, ENABLE);
	
//	USART_ITConfig(USART1, USART_IT_PE, ENABLE);
//	USART_ITConfig(USART1, USART_IT_ERR, ENABLE);

	USART_Cmd(USART1, ENABLE);  
}  
  
void tb_usart2_init(u32 rate) {  
	GPIO_InitTypeDef GPIO_InitStructure;  
    USART_InitTypeDef USART_InitStructure;   
	NVIC_InitTypeDef NVIC_InitStructure; 
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);  
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);  
    USART_DeInit(USART2);  
    /* Configure USART Tx as alternate function push-pull */  
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2;  
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;  
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;  
    GPIO_Init(GPIOA, &GPIO_InitStructure);  
      
    /* Configure USART Rx as input floating */  
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3;  
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;  
    GPIO_Init(GPIOA, &GPIO_InitStructure);  
	
    USART_InitStructure.USART_BaudRate = rate;  
    USART_InitStructure.USART_WordLength = USART_WordLength_8b;  
    USART_InitStructure.USART_StopBits = USART_StopBits_1;  
    USART_InitStructure.USART_Parity = USART_Parity_No;  
    USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;  
    USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;  
	USART_Init(USART2, &USART_InitStructure );   
	
	NVIC_InitStructure.NVIC_IRQChannel = USART2_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 2;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);   
	
	USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
    //USART_ITConfig(USART2, USART_IT_TXE, ENABLE);
	
//	USART_ITConfig(USART2, USART_IT_PE, ENABLE);
//	USART_ITConfig(USART2, USART_IT_ERR, ENABLE);
	
	USART_Cmd(USART2, ENABLE); 
} 

void tb_usart3_init(u32 rate) {  
	GPIO_InitTypeDef GPIO_InitStructure;  
    USART_InitTypeDef USART_InitStructure;   
	NVIC_InitTypeDef NVIC_InitStructure; 
	
	
	/* config USART3 clock */
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);
	
	/* USART3 GPIO config */
	/* Configure USART3 Tx (PB.10) as alternate function push-pull */
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOB, &GPIO_InitStructure);    
	
	/* Configure USART3 Rx (PB.11) as input floating */
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_11;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	GPIO_Init(GPIOB, &GPIO_InitStructure);
	
	/* USART3 mode config */
	USART_InitStructure.USART_BaudRate = rate;
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;
	USART_InitStructure.USART_StopBits = USART_StopBits_1;
	USART_InitStructure.USART_Parity = USART_Parity_No ;
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	USART_Init(USART3, &USART_InitStructure);
		
	NVIC_InitStructure.NVIC_IRQChannel = USART3_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 3;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);   
	
	USART_ITConfig(USART3, USART_IT_RXNE, ENABLE);
    //USART_ITConfig(USART3, USART_IT_TXE, ENABLE);
	
	USART_HalfDuplexCmd(USART3,ENABLE);
		
	USART_Cmd(USART3, ENABLE); 
} 

void tb_usart1_send_byte(u8 Data) {
	USART_SendData(USART1, Data);
	return;
}

void tb_usart1_send_nbyte(u8 *Data, u16 size) {
	u16 i = 0;
	for(i=0; i<size; i++) {
		USART_SendData(USART1, Data[i]);
		while(USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET); 
	}
	return;
}
void tb_usart1_send_str(u8 *Data) {
	while(*Data) {
		USART_SendData(USART1, *Data++);
		while(USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET); 
	}
	return;
}

void tb_usart2_send_byte(u8 Data) {
	USART_SendData(USART2, Data);
	return;
}

void tb_usart2_send_nbyte(u8 *Data, u16 size) {
	u16 i = 0;
	for(i=0; i<size; i++) {
		USART_SendData(USART2, Data[i]);
		while(USART_GetFlagStatus(USART2, USART_FLAG_TXE) == RESET); 
	}
	return;
}
void tb_usart2_send_str(u8 *Data) {
	while(*Data) {
		USART_SendData(USART2, *Data++);
		while(USART_GetFlagStatus(USART2, USART_FLAG_TXE) == RESET); 
	}
	return;
}

void tb_usart3_send_byte(u8 Data) {
	USART_SendData(USART3, Data);
	return;
}

void tb_usart3_send_nbyte(u8 *Data, u16 size) {
	u16 i = 0;
	for(i=0; i<size; i++) {
		USART_SendData(USART3, Data[i]);
		while(USART_GetFlagStatus(USART3, USART_FLAG_TXE) == RESET); 
	}
	return;
}
void tb_usart3_send_str(u8 *Data) {
	while(*Data) {
		USART_SendData(USART3, *Data++);
		while(USART_GetFlagStatus(USART3, USART_FLAG_TXE) == RESET); 
	}
	return;
}


/**========================串口中断=============================**/
int USART1_IRQHandler(void) {
	u8 sbuf_bak;
	static u16 buf_index = 0;

	if(USART_GetFlagStatus(USART1,USART_IT_RXNE)==SET) {
		USART_ClearITPendingBit(USART1, USART_IT_RXNE);		
		sbuf_bak = USART_ReceiveData(USART1); 

	}
	
	//if(USART_GetITStatus(USART1, USART_IT_TXE) != RESET) {   
		//USART_SendData(USARTy, TxBuffer1[TxCounter1++]);
	//}   
	return 0;
}

int USART2_IRQHandler(void) { 
	if(USART_GetFlagStatus(USART2,USART_IT_RXNE)==SET) {
		USART_ClearITPendingBit(USART2, USART_IT_RXNE);		
	
			
	}
	
	//if(USART_GetITStatus(USART2, USART_IT_TXE) != RESET) {   
	//	USART_SendData(USARTy, TxBuffer1[TxCounter1++]);
	//}  
	return 0;
}

int USART3_IRQHandler(void) { 
	u8 sbuf_bak;
	static u16 buf_index = 0;
	if(USART_GetFlagStatus(USART3,USART_IT_RXNE)==SET) {
		USART_ClearITPendingBit(USART3, USART_IT_RXNE);	
		sbuf_bak = USART_ReceiveData(USART3);			
	}
	
	//if(USART_GetITStatus(USART3, USART_IT_TXE) != RESET) {   
	//	USART_SendData(USARTy, TxBuffer1[TxCounter1++]);
	//}  
	return 0;
}



void uart1_send_str(u8 *str) {
	tb_usart1_send_str(str);
}

void uart1_send_nbyte(u8 *Data, u16 size) {
	tb_usart1_send_nbyte(Data, size);
}

void uart1_send_byte(u8 data) {
	tb_usart1_send_byte(data);
}



void uart2_send_str(u8 *str) {
	tb_usart2_send_str(str);	
}


void uart2_send_nbyte(u8 *Data, u16 size) {
	tb_usart2_send_nbyte(Data, size);
}

void uart2_send_byte(u8 data) {
	tb_usart2_send_byte(data);
}


void zx_uart_send_str(u8 *str) {
	tb_usart3_send_str(str);	
}


void uart3_send_str(u8 *str) {
	tb_usart3_send_str(str);	
}


void uart3_send_nbyte(u8 *Data, u16 size) {
	tb_usart3_send_nbyte(Data, size);
}

void uart3_send_byte(u8 data) {
	tb_usart3_send_byte(data);
}


